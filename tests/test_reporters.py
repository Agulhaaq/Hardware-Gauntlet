"""Unit tests for report generators in hwscan.reporters."""

import json
import os
import tempfile
import pytest
from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters import JSONReporter, MarkdownReporter, HTMLReporter, ConsoleReporter


@pytest.fixture(scope="module")
def sample_report():
    engine = HardwareScannerEngine()
    return engine.run_full_scan()


def test_json_reporter(sample_report):
    reporter = JSONReporter()
    json_str = reporter.to_json(sample_report)
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert "system" in data
    assert "cpu" in data
    assert "memory" in data
    assert "health_score" in data

    # Test file writing
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "report.json")
        reporter.write_file(sample_report, out_path)
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert saved_data["health_score"] == sample_report.health_score


def test_markdown_reporter(sample_report):
    reporter = MarkdownReporter()
    md_str = reporter.to_markdown(sample_report)
    assert isinstance(md_str, str)
    assert "Hardware Gauntlet Diagnostic Report" in md_str
    assert "Processor (CPU)" in md_str
    assert "Memory (RAM)" in md_str

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "report.md")
        reporter.write_file(sample_report, out_path)
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Hardware Gauntlet" in content


def test_html_reporter(sample_report):
    reporter = HTMLReporter()
    html_str = reporter.to_html(sample_report)
    assert isinstance(html_str, str)
    assert "<!DOCTYPE html>" in html_str
    assert "Hardware Gauntlet" in html_str
    assert "svg" in html_str.lower()
    assert str(sample_report.health_score) in html_str

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "report.html")
        reporter.write_file(sample_report, out_path)
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "report-data" in content


def test_console_reporter(sample_report):
    reporter = ConsoleReporter()
    # Test summary and full renders do not raise
    reporter.render(sample_report, full=False)
    reporter.render(sample_report, full=True)
