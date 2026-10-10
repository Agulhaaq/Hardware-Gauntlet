"""CPU Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import List

try:
    import psutil
except ImportError:
    psutil = None

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import CPUInfo
from hwscan.core.utils import run_command, run_powershell_json, format_bytes


class CPUScanner(BaseScanner):
    """Scans CPU processor specifications across Windows, Linux, and macOS."""

    def scan(self) -> CPUInfo:
        info = CPUInfo()
        info.architecture = platform.machine()
        
        # Current CPU usage
        if psutil:
            try:
                info.current_usage_percent = psutil.cpu_percent(interval=0.1)
                info.physical_cores = psutil.cpu_count(logical=False) or 1
                info.logical_cores = psutil.cpu_count(logical=True) or 1
            except Exception:
                pass

        current_system = platform.system().lower()
        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)
        else:
            info.model = platform.processor() or "Generic CPU"

        return info

    def _scan_windows(self, info: CPUInfo) -> None:
        try:
            raw_json = run_powershell_json(
                "Get-CimInstance Win32_Processor | Select-Object Name, Manufacturer, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, L2CacheSize, L3CacheSize"
            )
            if raw_json:
                data = json.loads(raw_json)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]

                info.model = data.get("Name", "").strip() or platform.processor()
                info.vendor = data.get("Manufacturer", "").strip()
                if not info.physical_cores and data.get("NumberOfCores"):
                    info.physical_cores = int(data.get("NumberOfCores"))
                if not info.logical_cores and data.get("NumberOfLogicalProcessors"):
                    info.logical_cores = int(data.get("NumberOfLogicalProcessors"))

                speed = data.get("MaxClockSpeed")
                if speed:
                    info.max_clock_mhz = float(speed)
                    info.base_clock_mhz = float(speed)

                l2 = data.get("L2CacheSize")
                if l2:
                    info.cache_l2 = format_bytes(int(l2) * 1024)
                l3 = data.get("L3CacheSize")
                if l3:
                    info.cache_l3 = format_bytes(int(l3) * 1024)
        except Exception:
            if not info.model or info.model == "Unknown":
                info.model = platform.processor()

        # Check features
        features = ["x86_64" if "64" in platform.machine() else "x86"]
        if "AMD" in (info.vendor or "").upper() or "AMD" in (info.model or "").upper():
            features.extend(["AMD-V", "AVX2", "SSE4.2", "AES-NI"])
        elif "INTEL" in (info.vendor or "").upper() or "INTEL" in (info.model or "").upper():
            features.extend(["VT-x", "AVX2", "SSE4.2", "AES-NI"])
        info.features = features

        # Query CPU package temperature if available
        try:
            if psutil and hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name in ["coretemp", "cpu_thermal", "k10temp", "zenpower", "cpu"]:
                        if name in temps and temps[name]:
                            info.temperature_c = float(temps[name][0].current)
                            break
            if info.temperature_c is None:
                out = run_command(
                    ["powershell.exe", "-NoProfile", "-Command",
                     "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature"],
                    timeout=3
                )
                if out and out.strip().isdigit():
                    k = int(out.strip())
                    c = (k - 2732) / 10.0
                    if 10 < c < 120:
                        info.temperature_c = round(c, 1)
        except Exception:
            pass

    def _scan_linux(self, info: CPUInfo) -> None:
        # Try lscpu --json first
        lscpu_out = run_command(["lscpu", "--json"])
        if lscpu_out:
            try:
                lscpu_data = json.loads(lscpu_out)
                entries = {item["field"].rstrip(":"): item["data"] for item in lscpu_data.get("lscpu", []) if "field" in item}
                info.model = entries.get("Model name", info.model)
                info.vendor = entries.get("Vendor ID", info.vendor)
                if "Core(s) per socket" in entries and "Socket(s)" in entries:
                    info.physical_cores = int(entries["Core(s) per socket"]) * int(entries["Socket(s)"])
                if "CPU(s)" in entries:
                    info.logical_cores = int(entries["CPU(s)"])
                if "CPU max MHz" in entries:
                    info.max_clock_mhz = float(entries["CPU max MHz"])
                if "L2 cache" in entries:
                    info.cache_l2 = entries["L2 cache"]
                if "L3 cache" in entries:
                    info.cache_l3 = entries["L3 cache"]
                if "Flags" in entries:
                    flags = entries["Flags"].split()
                    key_flags = [f for f in ["avx", "avx2", "avx512f", "sse4_2", "aes", "vmx", "svm"] if f in flags]
                    info.features = [f.upper() for f in key_flags]
            except Exception:
                pass

        # Fallback to /proc/cpuinfo
        if not info.model or info.model == "Unknown":
            if os.path.exists("/proc/cpuinfo"):
                try:
                    with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            if ":" in line:
                                k, v = [x.strip() for x in line.split(":", 1)]
                                if k == "model name" and info.model == "Unknown":
                                    info.model = v
                                elif k == "vendor_id" and info.vendor == "Unknown":
                                    info.vendor = v
                                elif k == "cpu MHz" and info.base_clock_mhz == 0:
                                    info.base_clock_mhz = float(v)
                                elif k == "flags" and not info.features:
                                    flags = v.split()
                                    info.features = [f.upper() for f in ["avx", "avx2", "sse4_2", "aes", "vmx", "svm"] if f in flags]
                except Exception:
                    pass

        try:
            if psutil and hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name in ["coretemp", "cpu_thermal", "k10temp", "zenpower", "cpu"]:
                        if name in temps and temps[name]:
                            info.temperature_c = float(temps[name][0].current)
                            break
        except Exception:
            pass

    def _scan_macos(self, info: CPUInfo) -> None:
        brand = run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
        if brand:
            info.model = brand
        else:
            # Apple Silicon fallback
            chip = run_command(["sysctl", "-n", "hw.model"])
            info.model = f"Apple Silicon ({chip})" if chip else "Apple Silicon"

        vendor = run_command(["sysctl", "-n", "machdep.cpu.vendor"])
        info.vendor = vendor if vendor else ("Apple" if "arm" in platform.machine().lower() else "Intel")

        p_cores = run_command(["sysctl", "-n", "hw.physicalcpu"])
        if p_cores and p_cores.isdigit():
            info.physical_cores = int(p_cores)

        l_cores = run_command(["sysctl", "-n", "hw.logicalcpu"])
        if l_cores and l_cores.isdigit():
            info.logical_cores = int(l_cores)

        max_hz = run_command(["sysctl", "-n", "hw.cpufrequency_max"])
        if max_hz and max_hz.isdigit():
            info.max_clock_mhz = float(max_hz) / 1_000_000.0

        features_str = run_command(["sysctl", "-n", "machdep.cpu.features"])
        if features_str:
            flags = features_str.split()
            info.features = [f for f in ["AVX1.0", "AVX2", "SSE4.2", "AES", "VMM"] if f in flags]
        elif "arm" in platform.machine().lower():
            info.features = ["ARMv8-A/ARMv9-A", "NEON", "Apple Neural Engine"]
