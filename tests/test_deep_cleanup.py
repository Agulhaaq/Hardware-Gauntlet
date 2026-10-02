"""Unit and integration tests for deep software & system cleanup engine."""

from unittest.mock import patch

from hwscan.core.deep_cleanup import (
    clean_component_store,
    clean_driver_and_kernel_store,
    optimize_system_storage_overhead,
    clean_developer_caches,
    run_deep_system_optimization
)


def test_clean_component_store():
    logs = []
    res = clean_component_store(log_fn=lambda m: logs.append(m))
    assert res["category"] == "component_store"
    assert res["success"] is True
    assert len(logs) > 0


def test_clean_driver_and_kernel_store():
    logs = []
    res = clean_driver_and_kernel_store(log_fn=lambda m: logs.append(m))
    assert res["category"] == "driver_store"
    assert res["success"] is True
    assert "packages_detected" in res
    assert len(logs) > 0


def test_optimize_system_storage_overhead():
    logs = []
    res = optimize_system_storage_overhead(log_fn=lambda m: logs.append(m))
    assert res["category"] == "storage_overhead"
    assert res["success"] is True
    assert len(logs) > 0


def test_clean_developer_caches():
    logs = []
    res = clean_developer_caches(log_fn=lambda m: logs.append(m))
    assert res["category"] == "developer_caches"
    assert res["success"] is True
    assert "tools_cleaned" in res
    assert len(logs) > 0


def test_run_deep_system_optimization():
    logs = []
    res = run_deep_system_optimization(log_fn=lambda m: logs.append(m))
    assert res["success"] is True
    assert "component_store" in res
    assert "driver_store" in res
    assert "storage_overhead" in res
    assert "developer_caches" in res
    assert any("ADVANCED DEEP SOFTWARE CLEANUP COMPLETE" in l for l in logs)


def test_deep_cleanup_linux_simulation():
    with patch("hwscan.core.deep_cleanup.get_current_os", return_value="linux"):
        logs = []
        res = run_deep_system_optimization(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "linux"


def test_deep_cleanup_macos_simulation():
    with patch("hwscan.core.deep_cleanup.get_current_os", return_value="macos"):
        logs = []
        res = run_deep_system_optimization(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "macos"


def test_deep_cleanup_admin_flag():
    with patch("hwscan.core.deep_cleanup.is_admin", return_value=False):
        logs = []
        res = clean_component_store(log_fn=lambda m: logs.append(m))
        assert res["admin"] is False
        assert res["success"] is True
