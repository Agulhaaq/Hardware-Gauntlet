"""Unit and integration tests for cross-platform system cleanup & optimization engine."""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from hwscan.core.cleanup import (
    clean_storage,
    clean_ram,
    clean_cpu,
    clean_network_cache,
    run_full_system_cleanup,
    _safe_remove_dir_contents
)


def test_safe_remove_dir_contents():
    with tempfile.TemporaryDirectory() as td:
        sub = os.path.join(td, "nested")
        os.makedirs(sub, exist_ok=True)
        f1 = os.path.join(td, "test1.tmp")
        f2 = os.path.join(sub, "test2.tmp")
        with open(f1, "w") as fp:
            fp.write("hello" * 100)
        with open(f2, "w") as fp:
            fp.write("world" * 100)

        bytes_freed, files_removed, dirs_removed = _safe_remove_dir_contents(td)
        assert bytes_freed == 1000
        assert files_removed == 2
        assert dirs_removed >= 1


def test_clean_storage():
    logs = []
    res = clean_storage(log_fn=lambda m: logs.append(m))
    assert res["category"] == "storage"
    assert res["success"] is True
    assert "freed_bytes" in res
    assert "freed_str" in res
    assert "files_removed" in res
    assert len(logs) > 0


def test_clean_ram():
    logs = []
    res = clean_ram(log_fn=lambda m: logs.append(m))
    assert res["category"] == "ram"
    assert res["success"] is True
    assert res["before_used"] > 0
    assert res["after_used"] > 0
    assert "reclaimed_bytes" in res
    assert "reclaimed_str" in res
    assert len(logs) > 0


def test_clean_cpu():
    logs = []
    res = clean_cpu(log_fn=lambda m: logs.append(m))
    assert res["category"] == "cpu"
    assert res["success"] is True
    assert res["processes_scanned"] > 0
    assert res["zombies_reaped"] >= 0
    assert len(logs) > 0


def test_clean_network_cache():
    logs = []
    res = clean_network_cache(log_fn=lambda m: logs.append(m))
    assert res["category"] == "network"
    assert res["success"] is True
    assert res["dns_flushed"] is True
    assert len(logs) > 0


def test_run_full_system_cleanup():
    logs = []
    res = run_full_system_cleanup(log_fn=lambda m: logs.append(m))
    assert res["success"] is True
    assert "storage" in res
    assert "ram" in res
    assert "cpu" in res
    assert "network" in res
    assert res["storage"]["success"] is True
    assert res["ram"]["success"] is True
    assert res["cpu"]["success"] is True
    assert res["network"]["success"] is True
    assert any("FULL SYSTEM OPTIMIZATION COMPLETE" in line for line in logs)


def test_cross_platform_linux_simulation():
    """Verify cleanup engine runs cleanly under simulated Linux environment."""
    with patch("hwscan.core.cleanup.get_current_os", return_value="linux"):
        logs = []
        res = run_full_system_cleanup(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "linux"


def test_cross_platform_macos_simulation():
    """Verify cleanup engine runs cleanly under simulated macOS environment."""
    with patch("hwscan.core.cleanup.get_current_os", return_value="macos"):
        logs = []
        res = run_full_system_cleanup(log_fn=lambda m: logs.append(m))
        assert res["success"] is True
        assert res["os"] == "macos"
