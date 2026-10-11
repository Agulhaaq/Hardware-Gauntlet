"""Integration tests for Hardware Gauntlet CLI and executables."""

import json
import os
import sys
import subprocess
import pytest


def test_cli_version_flag():
    result = subprocess.run(
        [sys.executable, "-m", "hwscan.cli", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Hardware Gauntlet" in result.stdout
    assert "v1.0.0" in result.stdout


def test_cli_health_check_flag():
    result = subprocess.run(
        [sys.executable, "-m", "hwscan.cli", "--health"],
        capture_output=True,
        text=True
    )
    assert result.returncode in (0, 1)
    assert "Hardware Health Score:" in result.stdout


def test_cli_json_stdout():
    result = subprocess.run(
        [sys.executable, "-m", "hwscan.cli", "--json", "-"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "system" in data
    assert "cpu" in data
    assert "memory" in data
    assert "health_score" in data


def test_cli_csv_stdout():
    result = subprocess.run(
        [sys.executable, "-m", "hwscan.cli", "--csv", "-"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Category,Subsystem,Property,Value,Unit_or_Details" in result.stdout
    assert "Operating System" in result.stdout
    assert "Processor" in result.stdout


def test_cli_bundle_and_ephemeral(tmp_path):
    bundle_target = str(tmp_path / "cli_test_bundle.zip")
    result = subprocess.run(
        [sys.executable, "-m", "hwscan.cli", "--ephemeral", "--bundle", bundle_target],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Complete diagnostic bundle archive generated:" in result.stdout
    assert os.path.exists(bundle_target)
    assert os.path.getsize(bundle_target) > 0


def test_dist_executables_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(base_dir, "dist")

    hg_exe = os.path.join(dist_dir, "HardwareGauntlet.exe")

    assert os.path.exists(hg_exe), f"Missing {hg_exe}"
    assert os.path.getsize(hg_exe) > 10_000_000


def test_root_executables_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_hg_exe = os.path.join(base_dir, "HardwareGauntlet.exe")

    assert os.path.exists(root_hg_exe), f"Missing {root_hg_exe}"
    assert os.path.getsize(root_hg_exe) > 10_000_000
