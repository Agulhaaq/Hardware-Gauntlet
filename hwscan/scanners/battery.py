"""Battery and Power Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import BatteryInfo
from hwscan.core.utils import run_command


class BatteryScanner(BaseScanner):
    """Scans battery health, charging status, and power supply."""

    def scan(self) -> BatteryInfo:
        info = BatteryInfo()

        if psutil:
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    info.has_battery = True
                    info.percent = round(bat.percent, 1)
                    info.power_plugged = bool(bat.power_plugged)
                    info.is_charging = bool(bat.power_plugged) and bat.percent < 100
                    if bat.secsleft > 0 and bat.secsleft != psutil.POWER_TIME_UNLIMITED:
                        info.time_remaining_seconds = bat.secsleft
            except Exception:
                pass

        # Try OS specific extra details (cycle count, health)
        current_system = platform.system().lower()
        if current_system == "darwin" and info.has_battery:
            self._scan_macos_battery(info)
        elif current_system == "linux" and info.has_battery:
            self._scan_linux_battery(info)

        return info

    def _scan_macos_battery(self, info: BatteryInfo) -> None:
        out = run_command(["system_profiler", "-json", "SPPowerDataType"])
        if out:
            try:
                data = json.loads(out)
                items = data.get("SPPowerDataType", [])
                for item in items:
                    info.cycle_count = item.get("sppower_battery_cycle_count")
                    info.health_status = item.get("sppower_battery_health", "Normal")
            except Exception:
                pass

    def _scan_linux_battery(self, info: BatteryInfo) -> None:
        bat_dir = "/sys/class/power_supply"
        if os.path.exists(bat_dir):
            for entry in os.listdir(bat_dir):
                if entry.startswith("BAT"):
                    base = os.path.join(bat_dir, entry)
                    cycle_file = os.path.join(base, "cycle_count")
                    if os.path.exists(cycle_file):
                        try:
                            with open(cycle_file, "r") as f:
                                info.cycle_count = int(f.read().strip())
                        except Exception:
                            pass
                    break
