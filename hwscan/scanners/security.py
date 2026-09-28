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
        # Secure Boot via Registry (accessible without admin rights)
        try:
            sb_val = run_command(
                "powershell.exe -NoProfile -Command \"(Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecureBoot\\State' -Name UEFISecureBootEnabled -ErrorAction SilentlyContinue)\"",
                shell=True
            ).strip()
            if sb_val == "1":
                info.secure_boot = True
            elif sb_val == "0":
                info.secure_boot = False
        except Exception:
            pass

        # Virtualization in Firmware
        try:
            virt_val = run_command(
                "powershell.exe -NoProfile -Command \"(Get-CimInstance Win32_Processor | Select-Object -First 1).VirtualizationFirmwareEnabled\"",
                shell=True
            ).strip()
            if virt_val.lower() == "true":
                info.virtualization_enabled = True
            elif virt_val.lower() == "false":
                info.virtualization_enabled = False
        except Exception:
            pass

        # TPM Status
        try:
            tpm_json = run_powershell_json(
                "Get-CimInstance -Namespace 'root\\cimv2\\Security\\MicrosoftTpm' -ClassName Win32_Tpm -ErrorAction SilentlyContinue | Select-Object IsEnabled_InitialValue, IsActivated_InitialValue, SpecVersion"
            )
            if tpm_json:
                data = json.loads(tpm_json)
                if isinstance(data, list) and data:
                    data = data[0]
                if data:
                    info.tpm_present = True
                    info.tpm_ready = bool(data.get("IsEnabled_InitialValue"))
                    spec = data.get("SpecVersion")
                    if spec:
                        info.tpm_version = str(spec).split(",")[0].strip()
            else:
                # Check device manager / registry for TPM
                tpm_reg = run_command(
                    "powershell.exe -NoProfile -Command \"(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\TPM' -ErrorAction SilentlyContinue) -ne $null\"",
                    shell=True
                ).strip()
                if tpm_reg.lower() == "true":
                    info.tpm_present = True
                    info.tpm_version = "2.0 (Detected)"
        except Exception:
            pass

    def _scan_linux(self, info: SecurityInfo) -> None:
        # Secure Boot via mokutil or efivars
        mok = run_command(["mokutil", "--sb-state"])
        if "SecureBoot enabled" in mok:
            info.secure_boot = True
        elif "SecureBoot disabled" in mok:
            info.secure_boot = False
        else:
            # Check efivars
            sb_file = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
            if os.path.exists(sb_file):
                try:
                    with open(sb_file, "rb") as f:
                        data = f.read()
                        if len(data) >= 5 and data[4] == 1:
                            info.secure_boot = True
                        else:
                            info.secure_boot = False
                except Exception:
                    pass

        # TPM
        if os.path.exists("/dev/tpm0") or os.path.exists("/sys/class/tpm/tpm0"):
            info.tpm_present = True
            info.tpm_ready = True
            if os.path.exists("/sys/class/tpm/tpm0/tpm_version_major"):
                try:
                    with open("/sys/class/tpm/tpm0/tpm_version_major", "r") as f:
                        info.tpm_version = f"{f.read().strip()}.0"
                except Exception:
                    info.tpm_version = "2.0"

        # Virtualization
        cpuinfo = run_command(["grep", "-E", "(vmx|svm)", "/proc/cpuinfo"])
        info.virtualization_enabled = bool(cpuinfo)

    def _scan_macos(self, info: SecurityInfo) -> None:
        # Apple Silicon has hardware enclave and secure boot built-in
        if "arm" in platform.machine().lower():
            info.secure_boot = True
            info.tpm_present = True
            info.tpm_version = "Apple Secure Enclave"
            info.virtualization_enabled = True
        else:
            # Intel Mac
            csr = run_command(["csrutil", "status"])
            info.secure_boot = "enabled" in csr.lower()
            info.virtualization_enabled = True
