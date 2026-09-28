"""Hardware Security Scanner (Secure Boot, TPM, Virtualization)."""

import os
import sys
import platform
import json
from typing import Optional

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import SecurityInfo
from hwscan.core.utils import run_command, run_powershell_json


class SecurityScanner(BaseScanner):
    """Scans hardware-level security attributes: Secure Boot, TPM 2.0, Virtualization."""

    def scan(self) -> SecurityInfo:
        info = SecurityInfo()
        current_system = platform.system().lower()

        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)

        return info

    def _scan_windows(self, info: SecurityInfo) -> None:
        # 1. Fast Secure Boot via direct Windows Registry (~0.0001s)
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SecureBoot\State") as k:
                val, _ = winreg.QueryValueEx(k, "UEFISecureBootEnabled")
                info.secure_boot = bool(val == 1)
        except Exception:
            pass

        # 2. Fast TPM detection via Registry (~0.0001s)
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\TPM") as k:
                info.tpm_present = True
                info.tpm_ready = True
                info.tpm_version = "2.0 (Detected)"
        except Exception:
            pass

        # 3. Virtualization detection via CPU features & hypervisor registry
        try:
            import winreg
            # Check hypervisor present flag or processor features
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization") as k:
                info.virtualization_enabled = True
        except Exception:
            pass

        if info.virtualization_enabled is None:
            # Fallback fast powershell query with short timeout (max 2s)
            try:
                virt = run_command(
                    "powershell.exe -NoProfile -Command \"(Get-CimInstance Win32_Processor | Select-Object -First 1).VirtualizationFirmwareEnabled\"",
                    timeout=2,
                    shell=True
                ).strip()
                if virt.lower() == "true":
                    info.virtualization_enabled = True
                elif virt.lower() == "false":
                    info.virtualization_enabled = False
            except Exception:
                info.virtualization_enabled = True

    def _scan_linux(self, info: SecurityInfo) -> None:
        mok = run_command(["mokutil", "--sb-state"])
        if "SecureBoot enabled" in mok:
            info.secure_boot = True
        elif "SecureBoot disabled" in mok:
            info.secure_boot = False
        else:
            sb_file = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
            if os.path.exists(sb_file):
                try:
                    with open(sb_file, "rb") as f:
                        data = f.read()
                        info.secure_boot = bool(len(data) >= 5 and data[4] == 1)
                except Exception:
                    pass

        if os.path.exists("/dev/tpm0") or os.path.exists("/sys/class/tpm/tpm0"):
            info.tpm_present = True
            info.tpm_ready = True
            if os.path.exists("/sys/class/tpm/tpm0/tpm_version_major"):
                try:
                    with open("/sys/class/tpm/tpm0/tpm_version_major", "r") as f:
                        info.tpm_version = f"{f.read().strip()}.0"
                except Exception:
                    info.tpm_version = "2.0"

        cpuinfo = run_command(["grep", "-E", "(vmx|svm)", "/proc/cpuinfo"])
        info.virtualization_enabled = bool(cpuinfo)

    def _scan_macos(self, info: SecurityInfo) -> None:
        if "arm" in platform.machine().lower():
            info.secure_boot = True
            info.tpm_present = True
            info.tpm_version = "Apple Secure Enclave"
            info.virtualization_enabled = True
        else:
            csr = run_command(["csrutil", "status"])
            info.secure_boot = "enabled" in csr.lower()
            info.virtualization_enabled = True
