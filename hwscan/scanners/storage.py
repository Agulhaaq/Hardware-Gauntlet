"""Storage (Physical Disks & Partitions) Scanner for Hardware Gauntlet."""

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
from hwscan.core.models import StorageInfo, PhysicalDisk, StoragePartition
from hwscan.core.utils import run_command, run_powershell_json, format_bytes


class StorageScanner(BaseScanner):
    """Scans physical drives (NVMe, SSD, HDD) and partition usage."""

    def scan(self) -> StorageInfo:
        info = StorageInfo()

        # Scan mounted partitions
        self._scan_partitions(info)

        # Scan physical drives
        current_system = platform.system().lower()
        if current_system == "windows":
            self._scan_windows_drives(info)
        elif current_system == "linux":
            self._scan_linux_drives(info)
        elif current_system == "darwin":
            self._scan_macos_drives(info)

        return info

    def _scan_partitions(self, info: StorageInfo) -> None:
        if not psutil:
            return

        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                # Filter out cdrom, dummy mounts, snap loops
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                if sys.platform != "win32" and (part.mountpoint.startswith("/snap") or part.mountpoint.startswith("/loop")):
                    continue

                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    p = StoragePartition(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total_bytes=usage.total,
                        total_formatted=format_bytes(usage.total),
                        used_bytes=usage.used,
                        used_formatted=format_bytes(usage.used),
                        free_bytes=usage.free,
                        free_formatted=format_bytes(usage.free),
                        percent=usage.percent
                    )
                    info.partitions.append(p)
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

    def _scan_windows_drives(self, info: StorageInfo) -> None:
        # First try Get-PhysicalDisk (modern Windows 10/11)
        try:
            raw_json = run_powershell_json(
                "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType, Size, SerialNumber, HealthStatus"
            )
            if raw_json:
                data = json.loads(raw_json)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    disk = PhysicalDisk()
                    disk.model = item.get("FriendlyName", "Unknown Drive").strip()
                    disk.media_type = item.get("MediaType", "SSD").strip()
                    disk.interface_type = item.get("BusType", "NVMe").strip()
                    disk.serial_number = item.get("SerialNumber", "Unknown").strip()
                    disk.smart_status = item.get("HealthStatus", "Healthy").strip()
                    sz = item.get("Size")
                    if sz:
                        disk.size_bytes = int(sz)
                        disk.size_formatted = format_bytes(disk.size_bytes)
                    info.physical_disks.append(disk)
                if info.physical_disks:
                    return
        except Exception:
            pass

        # Fallback to Win32_DiskDrive
        try:
            raw_json = run_powershell_json(
                "Get-CimInstance Win32_DiskDrive | Select-Object Model, InterfaceType, MediaType, Size, SerialNumber, Status"
            )
            if raw_json:
                data = json.loads(raw_json)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    disk = PhysicalDisk()
                    disk.model = item.get("Model", "Unknown Drive").strip()
                    disk.interface_type = item.get("InterfaceType", "SCSI/SATA").strip()
                    disk.media_type = item.get("MediaType", "Fixed Disk").strip()
                    disk.serial_number = item.get("SerialNumber", "Unknown").strip()
                    disk.smart_status = item.get("Status", "OK").strip()
                    sz = item.get("Size")
                    if sz:
                        disk.size_bytes = int(sz)
                        disk.size_formatted = format_bytes(disk.size_bytes)
                    info.physical_disks.append(disk)
        except Exception:
            pass

    def _scan_linux_drives(self, info: StorageInfo) -> None:
        out = run_command(["lsblk", "-J", "-b", "-o", "NAME,MODEL,SERIAL,SIZE,TYPE,ROTA"])
        if out:
            try:
                data = json.loads(out)
                blockdevices = data.get("blockdevices", [])
                for b in blockdevices:
                    if b.get("type") == "disk":
                        disk = PhysicalDisk()
                        disk.model = (b.get("model") or b.get("name") or "Disk").strip()
                        disk.serial_number = (b.get("serial") or "Unknown").strip()
                        sz = b.get("size")
                        if sz:
                            disk.size_bytes = int(sz)
                            disk.size_formatted = format_bytes(disk.size_bytes)
                        # ROTA: 0 = SSD/NVMe, 1 = HDD
                        rota = b.get("rota")
                        if str(rota) == "0":
                            disk.media_type = "NVMe/SSD"
                            disk.interface_type = "NVMe" if "nvme" in b.get("name", "").lower() else "SATA SSD"
                        else:
                            disk.media_type = "HDD"
                            disk.interface_type = "SATA HDD"
                        info.physical_disks.append(disk)
            except Exception:
                pass

    def _scan_macos_drives(self, info: StorageInfo) -> None:
        out = run_command(["system_profiler", "-json", "SPStorageDataType"])
        if out:
            try:
                data = json.loads(out)
                items = data.get("SPStorageDataType", [])
                for item in items:
                    disk = PhysicalDisk()
                    disk.model = item.get("_name", "Apple Internal Storage")
                    disk.media_type = "Apple Silicon / PCIe SSD"
                    disk.interface_type = "Apple Fabric / NVMe"
                    sz = item.get("size_in_bytes")
                    if sz:
                        disk.size_bytes = int(sz)
                        disk.size_formatted = format_bytes(disk.size_bytes)
                    info.physical_disks.append(disk)
            except Exception:
                pass
