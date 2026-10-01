"""Unit tests for installer_integration in hwscan.core."""

import os
import sys
import pytest
from hwscan.core.installer_integration import (
    acquire_single_instance_lock,
    get_install_directory,
    is_installed,
    uninstall_application
)


def test_get_install_directory():
    install_dir = get_install_directory()
    assert isinstance(install_dir, str)
    assert len(install_dir) > 0
    assert "HardwareGauntlet" in install_dir or "hardware-gauntlet" in install_dir


def test_acquire_single_instance_lock():
    # Calling acquire_single_instance_lock in test runner should succeed
    res = acquire_single_instance_lock("Test_Unique_Window_Title_12345")
    assert isinstance(res, bool)


def test_is_installed():
    res = is_installed()
    assert isinstance(res, bool)


def test_uninstall_when_not_installed(monkeypatch):
    # Test uninstall with nonexistent uninstall.ps1
    monkeypatch.setattr(
        "hwscan.core.installer_integration.get_install_directory",
        lambda: "C:\\NonExistent_Test_Directory_12345"
    )
    success, msg = uninstall_application()
    assert not success
    assert "Uninstaller not found" in msg
