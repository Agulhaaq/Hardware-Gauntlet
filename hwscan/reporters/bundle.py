"""Diagnostic Bundle Reporter for Hardware Gauntlet.

Packages full diagnostic telemetry into an encrypted or compressed .zip bundle
containing JSON data, HTML interactive report, CSV spreadsheet, TXT summary,
and runtime execution environment metadata.
"""

import os
import sys
import json
import zipfile
import datetime
import platform
from typing import Optional, Dict, Any

from hwscan import __version__, __app_name__
from hwscan.core.models import HardwareReport
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.csv_reporter import CSVReporter
from hwscan.core.utils import format_bytes, format_hz


class DiagnosticBundleReporter:
    """Exports comprehensive diagnostic bundles (.zip) for IT enterprise & support tickets."""

    def __init__(self):
        self.json_reporter = JSONReporter()
        self.html_reporter = HTMLReporter()
        self.csv_reporter = CSVReporter()

    def generate_summary_text(self, report: HardwareReport) -> str:
        """Create a clean human-readable plain-text hardware summary."""
        lines = [
            "=" * 72,
            f"  {__app_name__.upper()} v{__version__} — DIAGNOSTIC SYSTEM SUMMARY",
            "=" * 72,
            f"Timestamp    : {report.system.timestamp or datetime.datetime.now().isoformat()}",
            f"Hostname     : {report.system.hostname}",
            f"OS / Kernel  : {report.system.os_name} {report.system.os_version} ({report.system.os_arch})",
            f"Kernel Build : {report.system.kernel} (Build {report.system.os_build})",
            f"Uptime       : {report.system.uptime_formatted}",
            f"Health Score : {report.health_score} / 100",
            "-" * 72,
            "PROCESSOR (CPU):",
            f"  Model      : {report.cpu.model}",
            f"  Vendor     : {report.cpu.vendor}",
            f"  Topology   : {report.cpu.physical_cores} Physical Cores / {report.cpu.logical_cores} Threads",
            f"  Clock Base : {format_hz(report.cpu.base_clock_mhz)}",
            f"  Clock Max  : {format_hz(report.cpu.max_clock_mhz)}",
            f"  Caches     : L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}",
            "-" * 72,
            "MEMORY (RAM):",
            f"  Total RAM  : {format_bytes(report.memory.total_bytes)} ({format_bytes(report.memory.used_bytes)} Used, {report.memory.percent}%)",
            f"  DIMM Slots : {len(report.memory.modules)} Installed",
        ]

        for idx, m in enumerate(report.memory.modules, 1):
            lines.append(f"    Slot {idx}: {m.bank_label} - {m.capacity_formatted} {m.memory_type} @ {m.speed_mhz} MHz ({m.manufacturer} {m.part_number})")

        lines.extend([
            "-" * 72,
            "GRAPHICS ACCELERATORS (GPU):",
        ])
        for idx, g in enumerate(report.gpu.devices, 1):
            lines.append(f"  GPU #{idx}    : {g.name} ({g.vendor})")
            lines.append(f"    VRAM     : {g.vram_formatted}")
            lines.append(f"    Driver   : {g.driver_version or 'N/A'}")
            lines.append(f"    Display  : {g.resolution or 'No Active Display'}")

        lines.extend([
            "-" * 72,
            "STORAGE SUBSYSTEM:",
        ])
        for idx, d in enumerate(report.storage.physical_disks, 1):
            wear_str = f" | Wear: {d.wear_percent}%" if d.wear_percent is not None else ""
            lines.append(f"  Disk #{idx}   : {d.model} ({d.media_type} - {d.size_formatted} - {d.smart_status}{wear_str})")
        for idx, p in enumerate(report.storage.partitions, 1):
            lines.append(f"    Mount {p.mountpoint}: {p.fstype} | {p.used_formatted} / {p.total_formatted} ({p.percent}%)")

        lines.extend([
            "-" * 72,
            "SECURITY & FIRMWARE:",
            f"  Boot Mode  : {report.system.boot_mode}",
            f"  SecureBoot : {'ENABLED' if report.security.secure_boot else 'DISABLED'}",
            f"  TPM Module : {'PRESENT (' + (report.security.tpm_version or '2.0') + ')' if report.security.tpm_present else 'NOT DETECTED'}",
            f"  Hardware VT: {'ENABLED' if report.security.virtualization_enabled else 'DISABLED'}",
            "-" * 72,
            "SYSTEM WARNINGS & AUDIT FINDINGS:",
        ])
        if report.warnings:
            for w in report.warnings:
                lines.append(f"  [{w.level}] ({w.category}) {w.title}: {w.description}")
        else:
            lines.append("  [HEALTHY] No hardware faults or security anomalies detected.")

        lines.append("=" * 72)
        return "\n".join(lines) + "\n"

    def generate_environment_metadata(self) -> Dict[str, Any]:
        """Collect execution environment diagnostics."""
        return {
            "app_name": __app_name__,
            "app_version": __version__,
            "python_version": sys.version,
            "platform": platform.platform(),
            "executable_path": sys.executable,
            "is_frozen": getattr(sys, "frozen", False),
            "pid": os.getpid(),
            "exported_at": datetime.datetime.now().isoformat(),
        }

    def create_bundle(
        self,
        report: HardwareReport,
        output_zip: Optional[str] = None
    ) -> str:
        """Create a complete diagnostic bundle ZIP archive and return its path."""
        if not output_zip:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            hname = report.system.hostname or "Host"
            output_zip = f"HardwareGauntlet_Bundle_{hname}_{ts}.zip"

        output_zip = os.path.abspath(output_zip)
        parent_dir = os.path.dirname(output_zip)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        json_str = self.json_reporter.to_json(report)
        html_str = self.html_reporter.to_html(report)
        csv_str = self.csv_reporter.to_csv(report)
        summary_txt = self.generate_summary_text(report)
        env_meta = json.dumps(self.generate_environment_metadata(), indent=2)

        with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("hardware_report.json", json_str)
            zf.writestr("hardware_report.html", html_str)
            zf.writestr("hardware_report.csv", csv_str)
            zf.writestr("system_summary.txt", summary_txt)
            zf.writestr("environment_metadata.json", env_meta)

        return output_zip
