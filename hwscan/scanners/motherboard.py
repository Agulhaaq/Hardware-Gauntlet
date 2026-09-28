"""Motherboard and BIOS Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import Dict

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import MotherboardInfo
from hwscan.core.utils import run_command, run_powershell_json

CHASSIS_TYPES: Dict[int, str] = {
    1: "Other",
    2: "Unknown",
    3: "Desktop",
    4: "Low Profile Desktop",
    5: "Pizza Box",
    6: "Mini Tower",
    7: "Tower",
    8: "Portable",
    9: "Laptop",
    10: "Notebook",
    11: "Hand Held",
    12: "Docking Station",
    13: "All in One",
    14: "Sub Notebook",
    15: "Space-Saving",
    16: "Lunch Box",
    17: "Main Server Chassis",
    18: "Expansion Chassis",
    19: "SubChassis",
    20: "Bus Expansion Chassis",
    21: "Peripheral Chassis",
    22: "RAID Chassis",
    23: "Rack Mount Chassis",
    24: "Sealed-Case PC",
    30: "Tablet",
    31: "Convertible",
    32: "Detachable",
}


class MotherboardScanner(BaseScanner):
    """Scans Motherboard, BIOS, Serial, and Form Factor."""

    def scan(self) -> MotherboardInfo:
        info = MotherboardInfo()
        current_system = platform.system().lower()

        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)

        return info

    def _scan_windows(self, info: MotherboardInfo) -> None:
        # BaseBoard
        try:
            bb_json = run_powershell_json(
                "Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber, Version"
            )
            if bb_json:
                data = json.loads(bb_json)
                if isinstance(data, list) and data:
                    data = data[0]
                info.manufacturer = data.get("Manufacturer", "Unknown").strip()
                info.product_name = data.get("Product", "Unknown").strip()
                info.serial_number = data.get("SerialNumber", "Unknown").strip()
                info.version = data.get("Version", "").strip()
        except Exception:
            pass

        # BIOS
        try:
            bios_json = run_powershell_json(
                "Get-CimInstance Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate"
            )
            if bios_json:
                data = json.loads(bios_json)
                if isinstance(data, list) and data:
                    data = data[0]
                info.bios_vendor = data.get("Manufacturer", "Unknown").strip()
                info.bios_version = data.get("SMBIOSBIOSVersion", "Unknown").strip()
                rel = str(data.get("ReleaseDate", "")).strip()
                if rel:
                    if "/Date(" in rel:
                        try:
                            import re
                            from datetime import datetime, timezone
                            match = re.search(r"/Date\((\d+)\)/", rel)
                            if match:
                                ms = int(match.group(1))
                                dt = datetime.fromtimestamp(ms / 1000.0, timezone.utc)
                                info.bios_release_date = dt.strftime("%Y-%m-%d")
                            else:
                                info.bios_release_date = rel
                        except Exception:
                            info.bios_release_date = rel
                    else:
                        info.bios_release_date = rel.split("T")[0].split()[0]
        except Exception:
            pass

        # Chassis
        try:
            ch_json = run_powershell_json(
                "Get-CimInstance Win32_SystemEnclosure | Select-Object ChassisTypes"
            )
            if ch_json:
                data = json.loads(ch_json)
                ct = data.get("ChassisTypes", [])
                if isinstance(ct, list) and ct:
                    info.chassis_type = CHASSIS_TYPES.get(int(ct[0]), "Desktop/Laptop")
                elif isinstance(ct, int):
                    info.chassis_type = CHASSIS_TYPES.get(ct, "Desktop/Laptop")
        except Exception:
            pass

    def _scan_linux(self, info: MotherboardInfo) -> None:
        dmi_path = "/sys/class/dmi/id"
        if os.path.exists(dmi_path):
            def read_dmi(name: str) -> str:
                fp = os.path.join(dmi_path, name)
                if os.path.exists(fp):
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            return f.read().strip()
                    except Exception:
                        pass
                return ""

            info.manufacturer = read_dmi("board_vendor") or read_dmi("sys_vendor") or "Unknown"
            info.product_name = read_dmi("board_name") or read_dmi("product_name") or "Unknown"
            info.version = read_dmi("board_version") or read_dmi("product_version") or "Unknown"
            info.serial_number = read_dmi("board_serial") or read_dmi("product_serial") or "Unknown"
            info.bios_vendor = read_dmi("bios_vendor") or "Unknown"
            info.bios_version = read_dmi("bios_version") or "Unknown"
            info.bios_release_date = read_dmi("bios_date") or "Unknown"

            chassis_code = read_dmi("chassis_type")
            if chassis_code and chassis_code.isdigit():
                info.chassis_type = CHASSIS_TYPES.get(int(chassis_code), "Desktop/Server")

    def _scan_macos(self, info: MotherboardInfo) -> None:
        info.manufacturer = "Apple Inc."
        model_name = run_command(["sysctl", "-n", "hw.model"])
        info.product_name = model_name if model_name else "Mac Logic Board"

        out = run_command(["system_profiler", "-json", "SPHardwareDataType"])
        if out:
            try:
                data = json.loads(out)
                items = data.get("SPHardwareDataType", [])
                if items:
                    item = items[0]
                    info.product_name = item.get("machine_model", info.product_name)
                    info.serial_number = item.get("serial_number", "Apple Device")
                    info.bios_vendor = "Apple"
                    info.bios_version = item.get("boot_rom_version", item.get("os_loader_version", "Apple EFI"))
                    info.chassis_type = "Mac"
            except Exception:
                pass
