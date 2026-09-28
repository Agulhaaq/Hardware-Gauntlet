"""Console Reporter for Hardware Gauntlet with Rich UI and ASCII fallback."""

import sys
from typing import Optional
from hwscan.core.models import HardwareReport
from hwscan.core.utils import format_bytes, format_hz

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleReporter:
    """Renders HardwareReport onto the terminal with styling."""

    def __init__(self):
        if RICH_AVAILABLE:
            try:
                self.console = Console(safe_box=True, legacy_windows=False)
            except Exception:
                self.console = Console(safe_box=True)
        else:
            self.console = None

    def render(self, report: HardwareReport, full: bool = False) -> None:
        try:
            if RICH_AVAILABLE and self.console:
                self._render_rich(report, full)
            else:
                self._render_ascii(report, full)
        except Exception:
            # Fallback to plain ascii if terminal encoding throws
            self._render_ascii(report, full)

    def _render_rich(self, report: HardwareReport, full: bool) -> None:
        c = self.console
        
        # Header banner
        score_color = "bright_green" if report.health_score >= 85 else ("yellow" if report.health_score >= 70 else "bright_red")
        header_text = Text()
        header_text.append("[*] HARDWARE GAUNTLET ", style="bold bright_cyan")
        header_text.append("- Universal System Diagnostic Suite\n", style="white")
        header_text.append(f"Host: {report.system.hostname} | OS: {report.system.os_name} ({report.system.os_arch}) | Uptime: {report.system.uptime_formatted}\n", style="dim")
        header_text.append("Health Score: ", style="bold white")
        header_text.append(f"{report.health_score} / 100", style=f"bold {score_color}")
        header_text.append(f" (Scan completed in {report.scan_duration_seconds}s)", style="dim italic")

        c.print(Panel(header_text, border_style="bright_blue", box=box.ROUNDED))

        # 1. System & Motherboard
        sys_table = Table(title="[System & Motherboard]", box=box.ROUNDED, show_header=True, header_style="bold bright_cyan")
        sys_table.add_column("Component", style="bold white", width=22)
        sys_table.add_column("Specification / Value", style="green")

        sys_table.add_row("Operating System", f"{report.system.os_name} (Build {report.system.os_build})")
        sys_table.add_row("Kernel / Boot Mode", f"{report.system.kernel} | Boot: {report.system.boot_mode}")
        sys_table.add_row("Motherboard", f"{report.motherboard.manufacturer} {report.motherboard.product_name}")
        sys_table.add_row("Motherboard Serial", report.motherboard.serial_number or "N/A")
        sys_table.add_row("BIOS Vendor & Ver", f"{report.motherboard.bios_vendor} - v{report.motherboard.bios_version} ({report.motherboard.bios_release_date})")
        sys_table.add_row("Form Factor", report.motherboard.chassis_type)
        c.print(sys_table)

        # 2. CPU & Memory
        cpu_table = Table(title="[Processor & Memory]", box=box.ROUNDED, show_header=True, header_style="bold bright_cyan")
        cpu_table.add_column("Resource", style="bold white", width=22)
        cpu_table.add_column("Details", style="yellow")

        clock_str = f"{format_hz(report.cpu.max_clock_mhz)} (Base: {format_hz(report.cpu.base_clock_mhz)})" if report.cpu.max_clock_mhz else "N/A"
        cpu_table.add_row("Processor (CPU)", report.cpu.model)
        cpu_table.add_row("Cores & Threads", f"{report.cpu.physical_cores} Physical Cores / {report.cpu.logical_cores} Threads")
        cpu_table.add_row("Clock Speed", clock_str)
        cpu_table.add_row("Cache (L2 / L3)", f"L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}")
        cpu_table.add_row("CPU Load", f"{report.cpu.current_usage_percent}%")
        cpu_table.add_row("RAM Total & Usage", f"{format_bytes(report.memory.total_bytes)} total | {format_bytes(report.memory.used_bytes)} used ({report.memory.percent}%)")
        if report.memory.swap_total_bytes > 0:
            cpu_table.add_row("Swap / Pagefile", f"{format_bytes(report.memory.swap_total_bytes)} total | {format_bytes(report.memory.swap_used_bytes)} used ({report.memory.swap_percent}%)")
        
        # DIMM Modules
        if report.memory.modules:
            dimm_strs = []
            for m in report.memory.modules:
                dimm_strs.append(f"[{m.bank_label}]: {m.capacity_formatted} {m.memory_type} @ {m.speed_mhz}MHz ({m.manufacturer} {m.part_number})")
            cpu_table.add_row("Memory Sticks", "\n".join(dimm_strs))

        c.print(cpu_table)

        # 3. GPU & Displays
        if report.gpu.devices:
            gpu_table = Table(title="[Graphics (GPU) & Displays]", box=box.ROUNDED, show_header=True, header_style="bold bright_cyan")
            gpu_table.add_column("GPU Model", style="bold magenta", width=26)
            gpu_table.add_column("Vendor", style="white", width=12)
            gpu_table.add_column("VRAM", style="cyan", width=14)
            gpu_table.add_column("Driver Version", style="yellow", width=20)
            gpu_table.add_column("Display Mode", style="green")

            for dev in report.gpu.devices:
                gpu_table.add_row(
                    dev.name,
                    dev.vendor,
                    dev.vram_formatted,
                    dev.driver_version,
                    dev.resolution
                )
            c.print(gpu_table)

        # 4. Storage Disks & Partitions
        disk_table = Table(title="[Storage Drives & Partitions]", box=box.ROUNDED, show_header=True, header_style="bold bright_cyan")
        disk_table.add_column("Drive / Mount", style="bold white", width=18)
        disk_table.add_column("Type / Bus", style="cyan", width=16)
        disk_table.add_column("Capacity", style="white", width=12)
        disk_table.add_column("Used / Free", style="yellow", width=22)
        disk_table.add_column("Status / Bar", style="green")

        for disk in report.storage.physical_disks:
            disk_table.add_row(
                disk.model[:18],
                f"{disk.media_type} ({disk.interface_type})",
                disk.size_formatted,
                "Physical Disk",
                f"Health: {disk.smart_status}"
            )

        for part in report.storage.partitions:
            bar_len = 10
            filled = int((part.percent / 100.0) * bar_len)
            bar = "#" * filled + "-" * (bar_len - filled)
            part_color = "red" if part.percent > 85 else ("yellow" if part.percent > 70 else "green")
            disk_table.add_row(
                f"  +- {part.mountpoint}",
                part.fstype,
                part.total_formatted,
                f"{part.used_formatted} used ({part.free_formatted} free)",
                f"[{part_color}][{bar}] {part.percent}%[/{part_color}]"
            )
        c.print(disk_table)

        # 5. Network & Security Summary
        net_table = Table(title="[Network & Hardware Security]", box=box.ROUNDED, show_header=True, header_style="bold bright_cyan")
        net_table.add_column("Subsystem", style="bold white", width=22)
        net_table.add_column("Status & Details", style="white")

        active_ifs = [i for i in report.network.interfaces if i.is_up or i.ipv4]
        if active_ifs:
            for iface in active_ifs[:4]:
                ips = ", ".join(iface.ipv4) if iface.ipv4 else "No IPv4"
                speed_str = f" @ {iface.speed_mbps}Mbps" if iface.speed_mbps > 0 else ""
                net_table.add_row(f"Net: {iface.name}", f"{ips} | MAC: {iface.mac_address}{speed_str}")

        # Security
        sb_str = "[green]Enabled[/green]" if report.security.secure_boot else "[red]Disabled[/red]"
        tpm_str = f"[green]Present ({report.security.tpm_version or '2.0'})[/green]" if report.security.tpm_present else "[yellow]Not detected[/yellow]"
        virt_str = "[green]Enabled[/green]" if report.security.virtualization_enabled else "[yellow]Disabled / Unsupported[/yellow]"
        net_table.add_row("UEFI Secure Boot", sb_str)
        net_table.add_row("TPM 2.0 Security", tpm_str)
        net_table.add_row("Virtualization (VT/SVM)", virt_str)

        if report.battery.has_battery:
            chg = "Charging" if report.battery.is_charging else "On Battery"
            net_table.add_row("Battery", f"{report.battery.percent}% ({chg})")

        c.print(net_table)

        # 6. Diagnostics Warnings
        if report.warnings:
            warn_table = Table(title="[Hardware Health Diagnostics & Recommendations]", box=box.ROUNDED, header_style="bold yellow")
            warn_table.add_column("Level", width=12)
            warn_table.add_column("Category", width=14)
            warn_table.add_column("Issue & Recommendation")

            for w in report.warnings:
                lvl_style = "bold red" if w.level == "CRITICAL" else ("bold yellow" if w.level == "WARNING" else "cyan")
                warn_table.add_row(f"[{lvl_style}]{w.level}[/{lvl_style}]", w.category, f"[bold]{w.title}[/bold]: {w.description}")
            c.print(warn_table)

    def _render_ascii(self, report: HardwareReport, full: bool) -> None:
        print("=" * 70)
        print(f" HARDWARE GAUNTLET - Universal Hardware Diagnostic Suite")
        print(f" Host: {report.system.hostname} | OS: {report.system.os_name} ({report.system.os_arch})")
        print(f" Health Score: {report.health_score}/100 | Uptime: {report.system.uptime_formatted}")
        print("=" * 70)
        print(f"\n[CPU] {report.cpu.model}")
        print(f"      Cores: {report.cpu.physical_cores} Physical / {report.cpu.logical_cores} Threads | Usage: {report.cpu.current_usage_percent}%")
        print(f"\n[RAM] Total: {format_bytes(report.memory.total_bytes)} | Used: {format_bytes(report.memory.used_bytes)} ({report.memory.percent}%)")
        for m in report.memory.modules:
            print(f"      - {m.bank_label}: {m.capacity_formatted} {m.memory_type} @ {m.speed_mhz}MHz ({m.manufacturer})")
        print(f"\n[GPU]")
        for dev in report.gpu.devices:
            print(f"      - {dev.name} ({dev.vendor}) | VRAM: {dev.vram_formatted} | Driver: {dev.driver_version}")
        print(f"\n[STORAGE]")
        for p in report.storage.partitions:
            print(f"      - {p.mountpoint} [{p.fstype}]: {p.used_formatted} / {p.total_formatted} ({p.percent}%)")
        print(f"\n[SECURITY]")
        print(f"      Secure Boot: {'Enabled' if report.security.secure_boot else 'Disabled'}")
        print(f"      TPM 2.0: {'Present' if report.security.tpm_present else 'Not detected'}")
        print(f"      Virtualization: {'Enabled' if report.security.virtualization_enabled else 'Disabled'}")
        if report.warnings:
            print("\n[DIAGNOSTICS]")
            for w in report.warnings:
                print(f"      [{w.level}] {w.title}: {w.description}")
        print("=" * 70)
