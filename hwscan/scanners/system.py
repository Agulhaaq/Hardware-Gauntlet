"""System and OS scanner for Hardware Gauntlet."""

import os
import sys
import platform
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import SystemInfo
from hwscan.core.utils import run_command, format_uptime, is_admin


class SystemScanner(BaseScanner):
    """Scans operating system, kernel, boot mode, uptime, and identity."""

    def scan(self) -> SystemInfo:
        info = SystemInfo()
        info.hostname = platform.node() or "localhost"
        info.os_arch = platform.machine()
        info.is_admin = is_admin()
        info.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_system = platform.system().lower()

        # Uptime calculation
        uptime_sec = 0.0
        if psutil:
            try:
                uptime_sec = time.time() - psutil.boot_time()
            except Exception:
                pass
        
        if uptime_sec <= 0.0:
            uptime_sec = self._fallback_uptime()

        info.uptime_seconds = uptime_sec
        info.uptime_formatted = format_uptime(uptime_sec)

        # OS Details
        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "darwin":
            self._scan_macos(info)
        elif current_system == "linux":
            self._scan_linux(info)
        else:
            info.os_name = platform.system()
            info.os_version = platform.release()
            info.kernel = platform.version()

        return info

    def _fallback_uptime(self) -> float:
        try:
            if sys.platform == "win32":
                import ctypes
                return float(ctypes.windll.kernel32.GetTickCount64()) / 1000.0
            elif os.path.exists("/proc/uptime"):
                with open("/proc/uptime", "r") as f:
                    return float(f.readline().split()[0])
            else:
                out = run_command(["uptime"])
                return 0.0
        except Exception:
            return 0.0

    def _scan_windows(self, info: SystemInfo) -> None:
        info.os_name = f"Windows {platform.release()}"
        info.os_version = platform.release()
        info.os_build = platform.version()
        info.kernel = f"NT {platform.version()}"

        # Detect UEFI vs BIOS
        try:
            # Check registry for UEFI boot
            out = run_command(
                'powershell.exe -NoProfile -Command "(Get-ItemPropertyValue -Path \'HKLM:\\SYSTEM\\CurrentControlSet\\Control\' -Name PEFirmwareType -ErrorAction SilentlyContinue)"',
                shell=True
            )
            val = out.strip()
            if val == "2":
                info.boot_mode = "UEFI"
            elif val == "1":
                info.boot_mode = "Legacy BIOS"
            else:
                info.boot_mode = "UEFI" if os.path.exists(r"C:\Windows\Boot\EFI") else "BIOS"
        except Exception:
            info.boot_mode = "UEFI"

    def _scan_linux(self, info: SystemInfo) -> None:
        info.os_name = "Linux"
        info.kernel = platform.release()

        # Parse /etc/os-release
        if os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release", "r", encoding="utf-8", errors="replace") as f:
                    data = {}
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            data[k] = v.strip('"\'')
                    info.os_name = data.get("PRETTY_NAME", data.get("NAME", "Linux"))
                    info.os_version = data.get("VERSION_ID", data.get("VERSION", ""))
                    info.os_build = data.get("BUILD_ID", "")
            except Exception:
                pass

        # Boot mode
        if os.path.isdir("/sys/firmware/efi"):
            info.boot_mode = "UEFI"
        else:
            info.boot_mode = "Legacy BIOS"

    def _scan_macos(self, info: SystemInfo) -> None:
        ver = platform.mac_ver()[0]
        info.os_name = f"macOS {ver}" if ver else "macOS"
        info.os_version = ver
        info.kernel = f"Darwin {platform.release()}"
        info.boot_mode = "Apple EFI / iBoot"

        # Check sw_vers for build
        build = run_command(["sw_vers", "-buildVersion"])
        if build:
            info.os_build = build
