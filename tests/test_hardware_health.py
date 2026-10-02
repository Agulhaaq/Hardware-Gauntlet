"""Unit and integration tests for Phase 2: Hardware Health, Thermal Diagnostics & SSD Hygiene."""

from unittest.mock import patch, MagicMock

import pytest

from hwscan.core.hardware_health import (
    audit_thermal_health,
    audit_battery_longevity,
    optimize_ssd_trim,
    run_hardware_health_suite
)


def test_audit_thermal_health():
    logs = []
    res = audit_thermal_health(log_fn=lambda m: logs.append(m))
    assert res["category"] == "thermal_health"
    assert "status" in res
    assert "cpu_temp_c" in res
    assert "headroom_c" in res
    assert len(logs) > 0


def test_thermal_dust_detection_heuristic():
    logs = []
    # Test high temp under low CPU load (simulating dust/pump-out)
    res = audit_thermal_health(cpu_temp_override=88, cpu_load_override=10, log_fn=lambda m: logs.append(m))
    assert res["status"] == "HIGH_IDLE_TEMP_WARNING"
    assert res["dust_or_paste_warning"] is True
    assert any("dust" in l.lower() or "paste" in l.lower() for l in logs)


def test_audit_battery_longevity():
    logs = []
    res = audit_battery_longevity(log_fn=lambda m: logs.append(m))
    assert res["category"] == "battery_longevity"
    assert "has_battery" in res
    assert "recommendation" in res
    assert len(logs) > 0


def test_optimize_ssd_trim():
    logs = []
    res = optimize_ssd_trim(log_fn=lambda m: logs.append(m))
    assert res["category"] == "ssd_trim"
    assert "trim_supported" in res
    assert "free_space_percent" in res
    assert len(logs) > 0


def test_run_hardware_health_suite():
    logs = []
    res = run_hardware_health_suite(log_fn=lambda m: logs.append(m))
    assert res["success"] is True
    assert "thermal" in res
    assert "battery" in res
    assert "ssd" in res
    assert any("HARDWARE HEALTH & LONGEVITY AUDIT COMPLETE" in l for l in logs)


def test_hardware_health_linux_simulation():
    with patch("hwscan.core.hardware_health.get_current_os", return_value="linux"):
        logs = []
        res = run_hardware_health_suite(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "linux"


def test_hardware_health_macos_simulation():
    with patch("hwscan.core.hardware_health.get_current_os", return_value="macos"):
        logs = []
        res = run_hardware_health_suite(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "macos"
