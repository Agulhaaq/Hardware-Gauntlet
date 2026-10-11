"""Unit tests for DiagnosticBundleReporter."""

import os
import zipfile
import tempfile
import pytest

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.bundle import DiagnosticBundleReporter


@pytest.fixture(scope="module")
def sample_report():
    engine = HardwareScannerEngine()
    return engine.run_full_scan()


def test_bundle_reporter_creates_valid_zip(sample_report):
    reporter = DiagnosticBundleReporter()
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = os.path.join(tmpdir, "diagnostic_bundle.zip")
        result = reporter.create_bundle(sample_report, output_zip=bundle_path)

        assert os.path.exists(result)
        assert result == os.path.abspath(bundle_path)
        assert os.path.getsize(result) > 0

        # Verify ZIP contains all required artifacts
        with zipfile.ZipFile(result, "r") as zf:
            files = zf.namelist()
            assert "hardware_report.json" in files
            assert "hardware_report.html" in files
            assert "hardware_report.csv" in files
            assert "system_summary.txt" in files
            assert "environment_metadata.json" in files

            summary = zf.read("system_summary.txt").decode("utf-8")
            assert sample_report.system.hostname in summary

            json_content = zf.read("hardware_report.json").decode("utf-8")
            assert sample_report.system.hostname in json_content


def test_bundle_reporter_default_filename(sample_report):
    reporter = DiagnosticBundleReporter()
    bundle_path = reporter.create_bundle(sample_report)
    try:
        assert os.path.exists(bundle_path)
        assert f"HardwareGauntlet_Bundle_{sample_report.system.hostname}" in os.path.basename(bundle_path)
        assert bundle_path.endswith(".zip")
    finally:
        if os.path.exists(bundle_path):
            os.remove(bundle_path)
