"""CSV Exporter for Hardware Gauntlet.

Generates tabular CSV reports suitable for spreadsheet analysis,
IT asset management, and automated fleet inventory tracking.
"""

import csv
import io
from typing import List, Tuple
from hwscan.core.models import HardwareReport
from hwscan.core.utils import format_bytes, format_hz


class CSVReporter:
    """Exports HardwareReport as flattened CSV records."""

    HEADERS = ["Category", "Subsystem", "Property", "Value", "Unit_or_Details"]

    def to_rows(self, report: HardwareReport) -> List[Tuple[str, str, str, str, str]]:
        rows: List[Tuple[str, str, str, str, str]] = []

        # System Information
        sys_info = report.system
        rows.append(("System", "Operating System", "Hostname", str(sys_info.hostname), ""))
        rows.append(("System", "Operating System", "OS Name", str(sys_info.os_name), ""))
        rows.append(("System", "Operating System", "Version", str(sys_info.os_version), ""))
        rows.append(("System", "Operating System", "Build", str(sys_info.os_build), ""))
        rows.append(("System", "Operating System", "Architecture", str(sys_info.os_arch), ""))
        rows.append(("System", "Operating System", "Kernel", str(sys_info.kernel), ""))
        rows.append(("System", "Operating System", "Boot Mode", str(sys_info.boot_mode), ""))
        rows.append(("System", "Operating System", "Uptime", str(sys_info.uptime_formatted), f"{sys_info.uptime_seconds:.0f}s"))
        rows.append(("System", "Operating System", "Scan Timestamp", str(sys_info.timestamp), ""))

        # Diagnostics & Health
        rows.append(("Diagnostics", "Health", "Score", str(report.health_score), "/ 100"))
        rows.append(("Diagnostics", "Health", "Warning Count", str(len(report.warnings)), ""))
        for idx, w in enumerate(report.warnings, start=1):
            rows.append(("Diagnostics", f"Warning {idx}", str(w.title), str(w.description), str(w.level)))

        # Motherboard & BIOS
        mb = report.motherboard
        rows.append(("Motherboard", "Chassis & Board", "Manufacturer", str(mb.manufacturer), ""))
        rows.append(("Motherboard", "Chassis & Board", "Product Name", str(mb.product_name), ""))
        rows.append(("Motherboard", "Chassis & Board", "Serial Number", str(mb.serial_number), ""))
        rows.append(("Motherboard", "Chassis & Board", "Chassis Type", str(mb.chassis_type), ""))
        rows.append(("Motherboard", "BIOS", "Vendor", str(mb.bios_vendor), ""))
        rows.append(("Motherboard", "BIOS", "Version", str(mb.bios_version), ""))
        rows.append(("Motherboard", "BIOS", "Release Date", str(mb.bios_release_date), ""))

        # CPU
        cpu = report.cpu
        rows.append(("Processor", "CPU", "Model", str(cpu.model), ""))
        rows.append(("Processor", "CPU", "Vendor", str(cpu.vendor), ""))
        rows.append(("Processor", "CPU", "Architecture", str(cpu.architecture), ""))
        rows.append(("Processor", "CPU", "Physical Cores", str(cpu.physical_cores), "Cores"))
        rows.append(("Processor", "CPU", "Logical Cores", str(cpu.logical_cores), "Threads"))
        rows.append(("Processor", "CPU", "Base Clock", f"{cpu.base_clock_mhz:.0f}", "MHz"))
        rows.append(("Processor", "CPU", "Max Clock", f"{cpu.max_clock_mhz:.0f}", "MHz"))
        rows.append(("Processor", "CPU", "Usage Percent", f"{cpu.current_usage_percent:.1f}", "%"))
        rows.append(("Processor", "CPU", "L2 Cache", str(cpu.cache_l2), ""))
        rows.append(("Processor", "CPU", "L3 Cache", str(cpu.cache_l3), ""))
        if cpu.temperature_c is not None:
            rows.append(("Processor", "CPU", "Temperature", f"{cpu.temperature_c:.1f}", "°C"))
        if cpu.features:
            rows.append(("Processor", "CPU", "Instruction Sets", ", ".join(cpu.features[:15]), ""))

        # Memory (RAM)
        mem = report.memory
        rows.append(("Memory", "RAM Overview", "Total Capacity", format_bytes(mem.total_bytes), f"{mem.total_bytes} bytes"))
        rows.append(("Memory", "RAM Overview", "Used Memory", format_bytes(mem.used_bytes), f"{mem.used_bytes} bytes"))
        rows.append(("Memory", "RAM Overview", "Available Memory", format_bytes(mem.available_bytes), f"{mem.available_bytes} bytes"))
        rows.append(("Memory", "RAM Overview", "Usage Percent", f"{mem.percent:.1f}", "%"))
        rows.append(("Memory", "Swap", "Swap Total", format_bytes(mem.swap_total_bytes), ""))
        rows.append(("Memory", "Swap", "Swap Used", format_bytes(mem.swap_used_bytes), f"{mem.swap_percent:.1f}%"))

        for idx, mod in enumerate(mem.modules, start=1):
            slot_name = f"Slot {idx} ({mod.bank_label})"
            rows.append(("Memory", slot_name, "Capacity", str(mod.capacity_formatted), f"{mod.capacity_bytes} bytes"))
            rows.append(("Memory", slot_name, "Type", str(mod.memory_type), f"{mod.speed_mhz} MHz"))
            rows.append(("Memory", slot_name, "Manufacturer", str(mod.manufacturer), ""))
            rows.append(("Memory", slot_name, "Part Number", str(mod.part_number), ""))

        # Graphics (GPU)
        for idx, gpu in enumerate(report.gpu.devices, start=1):
            dev_name = f"GPU {idx} ({gpu.name})"
            rows.append(("Graphics", dev_name, "Name", str(gpu.name), ""))
            rows.append(("Graphics", dev_name, "Vendor", str(gpu.vendor), ""))
            rows.append(("Graphics", dev_name, "VRAM", str(gpu.vram_formatted), f"{gpu.vram_bytes} bytes"))
            rows.append(("Graphics", dev_name, "Driver Version", str(gpu.driver_version), ""))
            rows.append(("Graphics", dev_name, "Resolution", str(gpu.resolution), ""))

        # Storage (Physical Disks & Partitions)
        for idx, disk in enumerate(report.storage.physical_disks, start=1):
            disk_name = f"Physical Disk {idx}"
            rows.append(("Storage", disk_name, "Model", str(disk.model), ""))
            rows.append(("Storage", disk_name, "Media Type", str(disk.media_type), ""))
            rows.append(("Storage", disk_name, "Bus Interface", str(disk.interface_type), ""))
            rows.append(("Storage", disk_name, "Capacity", str(disk.size_formatted), f"{disk.size_bytes} bytes"))
            rows.append(("Storage", disk_name, "SMART Health", str(disk.smart_status), ""))
            rows.append(("Storage", disk_name, "Serial Number", str(disk.serial_number), ""))

        for part in report.storage.partitions:
            part_name = f"Partition {part.mountpoint or part.device}"
            rows.append(("Storage", part_name, "Mountpoint", str(part.mountpoint), ""))
            rows.append(("Storage", part_name, "Filesystem", str(part.fstype), ""))
            rows.append(("Storage", part_name, "Total", str(part.total_formatted), ""))
            rows.append(("Storage", part_name, "Used", str(part.used_formatted), f"{part.percent:.1f}%"))
            rows.append(("Storage", part_name, "Free", str(part.free_formatted), ""))

        # Network Interfaces
        for idx, net in enumerate(report.network.interfaces, start=1):
            if not net.is_up and not net.ipv4:
                continue
            iface_name = f"Interface {idx} ({net.name})"
            rows.append(("Network", iface_name, "Status", "Up" if net.is_up else "Down", "Wireless" if net.is_wireless else "Ethernet/Other"))
            rows.append(("Network", iface_name, "MAC Address", str(net.mac_address), ""))
            rows.append(("Network", iface_name, "IPv4", ", ".join(net.ipv4) if net.ipv4 else "N/A", ""))
            rows.append(("Network", iface_name, "Speed", f"{net.speed_mbps} Mbps" if net.speed_mbps > 0 else "N/A", ""))

        # Battery
        bat = report.battery
        if bat.has_battery:
            rows.append(("Power", "Battery", "Percent", f"{bat.percent:.1f}", "%"))
            rows.append(("Power", "Battery", "Status", "Charging" if bat.is_charging else "Discharging", "Plugged" if bat.power_plugged else "On Battery"))
            rows.append(("Power", "Battery", "Health", str(bat.health_status), ""))
            if bat.time_remaining_seconds is not None:
                mins = bat.time_remaining_seconds // 60
                rows.append(("Power", "Battery", "Time Remaining", f"{mins} mins", f"{bat.time_remaining_seconds}s"))
            if bat.cycle_count is not None:
                rows.append(("Power", "Battery", "Cycle Count", str(bat.cycle_count), "Cycles"))

        # Security
        sec = report.security
        rows.append(("Security", "Firmware & OS", "Secure Boot", "Enabled" if sec.secure_boot else "Disabled" if sec.secure_boot is False else "Unknown", ""))
        rows.append(("Security", "Firmware & OS", "TPM Present", "Yes" if sec.tpm_present else "No" if sec.tpm_present is False else "Unknown", str(sec.tpm_version or "")))
        if sec.tpm_ready is not None:
            rows.append(("Security", "Firmware & OS", "TPM Ready", "Yes" if sec.tpm_ready else "No", ""))
        rows.append(("Security", "Virtualization", "Hardware Virtualization", "Enabled" if sec.virtualization_enabled else "Disabled" if sec.virtualization_enabled is False else "Unknown", ""))

        # Peripherals
        peri = report.peripherals
        if peri.bluetooth_available is not None:
            rows.append(("Peripherals", "Connectivity", "Bluetooth", "Available" if peri.bluetooth_available else "Not Detected", ""))
        for idx, usb in enumerate(peri.usb_devices, start=1):
            rows.append(("Peripherals", f"USB Device {idx}", "Device Name", str(usb), ""))
        for idx, aud in enumerate(peri.audio_devices, start=1):
            rows.append(("Peripherals", f"Audio Device {idx}", "Device Name", str(aud), ""))

        return rows

    def to_csv(self, report: HardwareReport) -> str:
        """Convert HardwareReport to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(self.HEADERS)
        for row in self.to_rows(report):
            writer.writerow(row)
        return output.getvalue()

    def write_file(self, report: HardwareReport, filepath: str) -> None:
        """Write HardwareReport directly to a CSV file."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(self.HEADERS)
            for row in self.to_rows(report):
                writer.writerow(row)
