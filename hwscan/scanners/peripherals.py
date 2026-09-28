"""Peripherals Scanner (USB, Audio, Bluetooth) for Hardware Gauntlet."""

import os
import sys
import platform
import json
from typing import List

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import PeripheralInfo
from hwscan.core.utils import run_command, run_powershell_json


class PeripheralScanner(BaseScanner):
    """Scans USB devices, sound controllers, and bluetooth capability."""

    def scan(self) -> PeripheralInfo:
        info = PeripheralInfo()
        current_system = platform.system().lower()

        if current_system == "windows":
            self._scan_windows(info)
        elif current_system == "linux":
            self._scan_linux(info)
        elif current_system == "darwin":
            self._scan_macos(info)

        return info

    def _scan_windows(self, info: PeripheralInfo) -> None:
        # Audio devices
        try:
            snd_json = run_powershell_json(
                "Get-CimInstance Win32_SoundDevice | Select-Object Name, Manufacturer"
            )
            if snd_json:
                data = json.loads(snd_json)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("Name", "").strip()
                    if name and name not in info.audio_devices:
                        info.audio_devices.append(name)
        except Exception:
            pass

        # USB Devices
        try:
            usb_json = run_powershell_json(
                "Get-CimInstance Win32_USBHub | Select-Object Description"
            )
            if usb_json:
                data = json.loads(usb_json)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    desc = item.get("Description", "").strip()
                    if desc and desc not in info.usb_devices:
                        info.usb_devices.append(desc)
        except Exception:
            pass

        # Bluetooth check
        try:
            bt_check = run_powershell_json(
                "Get-Service bthserv -ErrorAction SilentlyContinue | Select-Object Status"
            )
            if bt_check:
                info.bluetooth_available = True
        except Exception:
            pass

    def _scan_linux(self, info: PeripheralInfo) -> None:
        # USB via lsusb
        lsusb = run_command(["lsusb"])
        if lsusb:
            for line in lsusb.splitlines():
                if "ID " in line:
                    parts = line.split("ID ", 1)
                    if len(parts) > 1:
                        info.usb_devices.append(parts[1].strip())

        # Audio via aplay
        aplay = run_command(["aplay", "-l"])
        if aplay:
            for line in aplay.splitlines():
                if line.startswith("card "):
                    info.audio_devices.append(line.strip())

        # Bluetooth check
        info.bluetooth_available = os.path.exists("/sys/class/bluetooth") or bool(run_command(["rfkill", "list", "bluetooth"]))

    def _scan_macos(self, info: PeripheralInfo) -> None:
        # USB
        out_usb = run_command(["system_profiler", "-json", "SPUSBDataType"])
        if out_usb:
            try:
                data = json.loads(out_usb)
                items = data.get("SPUSBDataType", [])
                for item in items:
                    name = item.get("_name")
                    if name:
                        info.usb_devices.append(name)
            except Exception:
                pass

        # Audio
        out_audio = run_command(["system_profiler", "-json", "SPAudioDataType"])
        if out_audio:
            try:
                data = json.loads(out_audio)
                items = data.get("SPAudioDataType", [])
                for item in items:
                    name = item.get("_name")
                    if name:
                        info.audio_devices.append(name)
            except Exception:
                pass

        # Bluetooth
        out_bt = run_command(["system_profiler", "SPBluetoothDataType"])
        if out_bt and "Bluetooth Power: On" in out_bt:
            info.bluetooth_available = True
