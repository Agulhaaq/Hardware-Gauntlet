"""Memory (RAM & Swap) Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import List, Dict

try:
    import psutil
except ImportError:
    psutil = None

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import MemoryInfo, MemoryModule
from hwscan.core.utils import run_command, run_powershell_json, format_bytes

# SMBIOS Memory Types standard lookup
SMBIOS_MEMORY_TYPES: Dict[int, str] = {
    20: "DDR",
    21: "DDR2",
    22: "DDR2 FB-DIMM",
    24: "DDR3",
    26: "DDR4",
    27: "LPDDR",
    28: "LPDDR2",
    29: "LPDDR3",
    30: "LPDDR4",
    34: "DDR5",
    35: "LPDDR5",
}

SMBIOS_FORM_FACTORS: Dict[int, str] = {
    8: "DIMM (Desktop)",
    12: "SODIMM (Laptop)",
    13: "SRIMM",
    14: "SMD",
    15: "SSMP",
}


class MemoryScanner(BaseScanner):
    """Scans physical memory, DIMM modules, and swap space."""

    def scan(self) -> MemoryInfo:
        info = MemoryInfo()

        # Global RAM stats using psutil
        if psutil:
            try:
                vm = psutil.virtual_memory()
                info.total_bytes = vm.total
                info.available_bytes = vm.available
                info.used_bytes = vm.used
                info.percent = vm.percent

                swap = psutil.swap_memory()
                info.swap_total_bytes = swap.total
                info.swap_used_bytes = swap.used
                info.swap_percent = swap.percent
            except Exception:
                pass

        current_system = platform.system().lower()
        if current_system == "windows":
            self._scan_windows_modules(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)

        return info

    def _scan_windows_modules(self, info: MemoryInfo) -> None:
        try:
            raw_json = run_powershell_json(
                "Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, Capacity, Speed, ConfiguredClockSpeed, SMBIOSMemoryType, PartNumber, DeviceLocator, FormFactor"
            )
            if not raw_json:
                return

            data = json.loads(raw_json)
            if isinstance(data, dict):
                data = [data]

            for idx, item in enumerate(data):
                mod = MemoryModule()
                mod.bank_label = item.get("DeviceLocator") or f"Slot {idx + 1}"
                cap = item.get("Capacity")
                if cap:
                    mod.capacity_bytes = int(cap)
                    mod.capacity_formatted = format_bytes(mod.capacity_bytes)

                speed = item.get("ConfiguredClockSpeed") or item.get("Speed") or 0
                mod.speed_mhz = int(speed)

                smbios_type = item.get("SMBIOSMemoryType", 0)
                mod.memory_type = SMBIOS_MEMORY_TYPES.get(smbios_type, "DDR4" if mod.speed_mhz >= 2133 else "RAM")

                ff = item.get("FormFactor", 0)
                mod.form_factor = SMBIOS_FORM_FACTORS.get(ff, "DIMM")

                mfg = item.get("Manufacturer", "").strip()
                mod.manufacturer = mfg if mfg and mfg.lower() != "unknown" else "OEM"

                part = item.get("PartNumber", "").strip()
                mod.part_number = part if part else "N/A"

                info.modules.append(mod)
        except Exception:
            pass

    def _scan_linux(self, info: MemoryInfo) -> None:
        # Fallback for total if psutil missing
        if info.total_bytes == 0 and os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r") as f:
                    mem_data = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            val = parts[1].strip().split()[0]
                            mem_data[parts[0].strip()] = int(val) * 1024
                    info.total_bytes = mem_data.get("MemTotal", 0)
                    info.available_bytes = mem_data.get("MemAvailable", 0)
                    info.used_bytes = info.total_bytes - info.available_bytes
                    if info.total_bytes > 0:
                        info.percent = round((info.used_bytes / info.total_bytes) * 100, 1)
            except Exception:
                pass

        # Try dmidecode for modules if elevated / available
        dmi = run_command(["dmidecode", "-t", "memory"])
        if dmi and "Memory Device" in dmi:
            self._parse_dmidecode(dmi, info)

    def _parse_dmidecode(self, output: str, info: MemoryInfo) -> None:
        devices = output.split("Memory Device")
        for dev in devices[1:]:
            lines = dev.strip().split("\n")
            fields = {}
            for line in lines:
                if ":" in line:
                    k, v = [x.strip() for x in line.split(":", 1)]
                    fields[k] = v

            size_str = fields.get("Size", "")
            if not size_str or "No Module Installed" in size_str:
                continue

            mod = MemoryModule()
            mod.bank_label = fields.get("Locator", "DIMM")
            mod.manufacturer = fields.get("Manufacturer", "Unknown")
            mod.part_number = fields.get("Part Number", "Unknown")
            mod.memory_type = fields.get("Type", "DDR")
            speed_str = fields.get("Speed", "")
            if "MT/s" in speed_str or "MHz" in speed_str:
                digits = "".join(c for c in speed_str if c.isdigit())
                if digits:
                    mod.speed_mhz = int(digits)
            info.modules.append(mod)

    def _scan_macos(self, info: MemoryInfo) -> None:
        out = run_command(["system_profiler", "-json", "SPMemoryDataType"])
        if not out:
            return
        try:
            data = json.loads(out)
            mem_items = data.get("SPMemoryDataType", [])
            for item in mem_items:
                # May have memory slots array
                slots = item.get("_items", [])
                for s in slots:
                    mod = MemoryModule()
                    mod.bank_label = s.get("dimm_name", "DIMM")
                    mod.capacity_formatted = s.get("dimm_size", "N/A")
                    mod.memory_type = s.get("dimm_type", "Unified LPDDR")
                    mod.manufacturer = s.get("dimm_manufacturer", "Apple")
                    mod.part_number = s.get("dimm_part_number", "N/A")
                    speed_s = s.get("dimm_speed", "")
                    digits = "".join(c for c in speed_s if c.isdigit())
                    if digits:
                        mod.speed_mhz = int(digits)
                    info.modules.append(mod)
        except Exception:
            pass
