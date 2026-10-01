"""Unit tests for HardwareScannerEngine."""

import unittest
from hwscan.core.system_info import HardwareScannerEngine
from hwscan.core.models import HardwareReport


class TestEngine(unittest.TestCase):
    def test_run_full_scan(self):
        engine = HardwareScannerEngine()
        report = engine.run_full_scan()

        self.assertIsInstance(report, HardwareReport)
        self.assertGreater(report.scan_duration_seconds, 0)
        self.assertGreaterEqual(report.health_score, 0)
        self.assertLessEqual(report.health_score, 100)
        self.assertIsInstance(report.warnings, list)

        # Check sub-models populated
        self.assertNotEqual(report.system.hostname, "")
        self.assertGreater(report.cpu.logical_cores, 0)
        self.assertGreater(report.memory.total_bytes, 0)
        self.assertGreater(len(report.storage.partitions), 0)


if __name__ == "__main__":
    unittest.main()
