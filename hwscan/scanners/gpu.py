"""Graphics (GPU) & Display Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import List

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import GPUInfo, GPUDevice
from hwscan.core.utils import run_command, run_powershell_json, format_bytes


class GPUScanner(BaseScanner):
    """Scans GPU adapters, VRAM, drivers, and display resolutions."""

    def scan(self) -> GPUInfo:
        info = GPUInfo()
        current_system = platform.system().lower()

        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)

        # Check nvidia-smi enhancements for all OSes
        self._enhance_with_nvidia_smi(info)

        return info

    def _scan_windows(self, info: GPUInfo) -> None:
        try:
            raw_json = run_powershell_json(
                "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate"
            )
            if not raw_json:
                return

            data = json.loads(raw_json)
            if isinstance(data, dict):
                data = [data]

            for item in data:
                name = item.get("Name", "").strip()
                if not name:
                    continue

                # Filter out remote desktop / virtual mirror drivers unless it's the only one
                if "Virtual" in name and len(data) > 1 and any("GeForce" in x.get("Name", "") or "Radeon" in x.get("Name", "") or "Intel" in x.get("Name", "") for x in data):
                    continue

                gpu = GPUDevice()
                gpu.name = name
                gpu.driver_version = item.get("DriverVersion", "Unknown")
                gpu.video_processor = item.get("VideoProcessor", name)

                # Vendor determination
                up = name.upper()
                if "NVIDIA" in up:
                    gpu.vendor = "NVIDIA"
                elif "AMD" in up or "RADEON" in up:
                    gpu.vendor = "AMD"
                elif "INTEL" in up:
                    gpu.vendor = "Intel"
                else:
                    gpu.vendor = "Generic"

                ram = item.get("AdapterRAM")
                if ram:
                    try:
                        vram_int = int(ram)
                        if vram_int > 0:
                            gpu.vram_bytes = vram_int
                            gpu.vram_formatted = format_bytes(vram_int)
                    except Exception:
                        pass

                w = item.get("CurrentHorizontalResolution")
                h = item.get("CurrentVerticalResolution")
                hz = item.get("CurrentRefreshRate")
                if w and h:
                    gpu.resolution = f"{w}x{h}" + (f" @ {hz}Hz" if hz else "")

                info.devices.append(gpu)
        except Exception:
            pass

    def _enhance_with_nvidia_smi(self, info: GPUInfo) -> None:
        """Query nvidia-smi to obtain exact hardware VRAM if 32-bit WMI truncated it."""
        try:
            out = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits", shell=True)
            if not out:
                return
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    nv_name = parts[0]
                    vram_mb = parts[1]
                    driver = parts[2] if len(parts) > 2 else ""

                    matched = False
                    for dev in info.devices:
                        if "NVIDIA" in dev.vendor or dev.name.lower() in nv_name.lower() or nv_name.lower() in dev.name.lower():
                            if vram_mb.isdigit():
                                dev.vram_bytes = int(vram_mb) * 1024 * 1024
                                dev.vram_formatted = format_bytes(dev.vram_bytes)
                            if driver and dev.driver_version in ("Unknown", ""):
                                dev.driver_version = driver
                            matched = True
                            break

                    if not matched:
                        dev = GPUDevice()
                        dev.name = nv_name
                        dev.vendor = "NVIDIA"
                        if vram_mb.isdigit():
                            dev.vram_bytes = int(vram_mb) * 1024 * 1024
                            dev.vram_formatted = format_bytes(dev.vram_bytes)
                        if driver:
                            dev.driver_version = driver
                        info.devices.append(dev)
        except Exception:
            pass

    def _scan_linux(self, info: GPUInfo) -> None:
        # Check lspci
        lspci_out = run_command(["lspci", "-nnk"])
        if lspci_out:
            lines = lspci_out.splitlines()
            current_device = None
            for line in lines:
                if any(tag in line.lower() for tag in ["vga compatible controller", "3d controller", "display controller"]):
                    parts = line.split(":", 2)
                    name = parts[2].strip() if len(parts) >= 3 else line
                    dev = GPUDevice(name=name)
                    if "nvidia" in name.lower():
                        dev.vendor = "NVIDIA"
                    elif "amd" in name.lower() or "advanced micro devices" in name.lower():
                        dev.vendor = "AMD"
                    elif "intel" in name.lower():
                        dev.vendor = "Intel"
                    info.devices.append(dev)
                    current_device = dev
                elif current_device and "kernel driver in use:" in line.lower():
                    drv = line.split(":")[-1].strip()
                    current_device.driver_version = f"Kernel driver: {drv}"

    def _scan_macos(self, info: GPUInfo) -> None:
        out = run_command(["system_profiler", "-json", "SPDisplaysDataType"])
        if not out:
            return
        try:
            data = json.loads(out)
            items = data.get("SPDisplaysDataType", [])
            for item in items:
                dev = GPUDevice()
                dev.name = item.get("sppci_model", item.get("_name", "Apple GPU"))
                dev.vendor = item.get("spdisplays_vendor", "Apple")
                vram_s = item.get("spdisplays_vram", item.get("spdisplays_vram_shared", ""))
                dev.vram_formatted = vram_s if vram_s else "Unified Memory"
                res = item.get("spdisplays_resolution", "")
                if res:
                    dev.resolution = res
                info.devices.append(dev)
        except Exception:
            pass
