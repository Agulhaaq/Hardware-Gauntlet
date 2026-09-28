"""Markdown Report Exporter for Hardware Gauntlet."""

from hwscan.core.models import HardwareReport
from hwscan.core.utils import format_bytes, format_hz


class MarkdownReporter:
    """Generates clean GitHub Flavored Markdown diagnostic reports."""

    def to_markdown(self, report: HardwareReport) -> str:
        md = []
        md.append(f"# ⚡ Hardware Gauntlet Diagnostic Report")
        md.append(f"**Generated:** {report.system.timestamp}  ")
        md.append(f"**Host:** `{report.system.hostname}` | **OS:** {report.system.os_name} ({report.system.os_arch})  ")
        md.append(f"**Health Score:** **{report.health_score} / 100**  ")
        md.append("")

        # Diagnostics Warnings
        if report.warnings:
            md.append("## ⚠️ Diagnostics & Health Findings")
            for w in report.warnings:
                icon = "🔴" if w.level == "CRITICAL" else ("🟡" if w.level == "WARNING" else "🔵")
                md.append(f"- {icon} **[{w.level}] {w.title}**: {w.description}")
            md.append("")

        # System Overview
        md.append("## 🖥️ System & Motherboard")
        md.append("| Property | Value |")
        md.append("| :--- | :--- |")
        md.append(f"| Operating System | {report.system.os_name} (Build {report.system.os_build}) |")
        md.append(f"| Kernel | {report.system.kernel} |")
        md.append(f"| Boot Mode | {report.system.boot_mode} |")
        md.append(f"| Motherboard | {report.motherboard.manufacturer} {report.motherboard.product_name} |")
        md.append(f"| BIOS | {report.motherboard.bios_vendor} {report.motherboard.bios_version} ({report.motherboard.bios_release_date}) |")
        md.append(f"| Uptime | {report.system.uptime_formatted} |")
        md.append("")

        # Processor (CPU)
        md.append("## 🧠 Processor (CPU)")
        md.append(f"- **Model:** {report.cpu.model}")
        md.append(f"- **Cores / Threads:** {report.cpu.physical_cores} Physical Cores / {report.cpu.logical_cores} Threads")
        md.append(f"- **Max Clock:** {format_hz(report.cpu.max_clock_mhz)}")
        md.append(f"- **Cache:** L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}")
        md.append(f"- **Features:** {', '.join(report.cpu.features)}")
        md.append("")

        # Memory (RAM)
        md.append("## 📊 Memory (RAM)")
        md.append(f"- **Total Capacity:** {format_bytes(report.memory.total_bytes)}")
        md.append(f"- **Usage:** {format_bytes(report.memory.used_bytes)} used ({report.memory.percent}%)")
        if report.memory.modules:
            md.append("\n### Physical Memory Modules")
            md.append("| Slot | Capacity | Type | Speed | Manufacturer | Part Number |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for m in report.memory.modules:
                md.append(f"| {m.bank_label} | {m.capacity_formatted} | {m.memory_type} | {m.speed_mhz} MHz | {m.manufacturer} | {m.part_number} |")
        md.append("")

        # Graphics (GPU)
        if report.gpu.devices:
            md.append("## 🎮 Graphics (GPU)")
            md.append("| GPU Device | Vendor | VRAM | Driver | Resolution |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for g in report.gpu.devices:
                md.append(f"| {g.name} | {g.vendor} | {g.vram_formatted} | {g.driver_version} | {g.resolution} |")
            md.append("")

        # Storage
        md.append("## 💾 Storage")
        if report.storage.physical_disks:
            md.append("### Physical Disks")
            md.append("| Model | Type | Bus | Size | Status |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for d in report.storage.physical_disks:
                md.append(f"| {d.model} | {d.media_type} | {d.interface_type} | {d.size_formatted} | {d.smart_status} |")
            md.append("")

        if report.storage.partitions:
            md.append("### Mounted Partitions")
            md.append("| Mount | Filesystem | Used / Total | Percent | Free |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for p in report.storage.partitions:
                md.append(f"| `{p.mountpoint}` | {p.fstype} | {p.used_formatted} / {p.total_formatted} | {p.percent}% | {p.free_formatted} |")
            md.append("")

        # Security
        md.append("## 🔒 Hardware Security")
        md.append(f"- **UEFI Secure Boot:** {'Enabled' if report.security.secure_boot else 'Disabled'}")
        md.append(f"- **TPM 2.0:** {'Present' if report.security.tpm_present else 'Not Detected'} ({report.security.tpm_version or 'N/A'})")
        md.append(f"- **Virtualization Support:** {'Enabled' if report.security.virtualization_enabled else 'Disabled'}")
        md.append("")

        return "\n".join(md)

    def write_file(self, report: HardwareReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_markdown(report))
