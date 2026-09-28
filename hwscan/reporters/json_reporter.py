"""JSON Exporter for Hardware Gauntlet."""

import json
from typing import Optional
from hwscan.core.models import HardwareReport


class JSONReporter:
    """Exports HardwareReport as structured JSON."""

    def to_json(self, report: HardwareReport, indent: int = 2) -> str:
        return json.dumps(report.to_dict(), indent=indent, default=str)

    def write_file(self, report: HardwareReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json(report))
