"""Unit tests for standalone single-instance mutex and window management."""

import pytest
from hwscan.core.installer_integration import (
    acquire_single_instance_lock,
    release_single_instance_lock,
    find_existing_window,
    focus_window,
    WINDOW_TITLE
)


def test_window_title_constant():
    assert "Hardware Gauntlet" in WINDOW_TITLE


def test_acquire_and_release_single_instance_lock():
    res = acquire_single_instance_lock("Test_Unique_Window_Title_12345")
    assert isinstance(res, bool)
    release_single_instance_lock()


def test_find_and_focus_window():
    # Searching for nonexistent window should return None safely
    hwnd = find_existing_window("Nonexistent_Window_Title_XYZ_99999")
    assert hwnd is None
    # Calling focus_window with None or 0 should not raise
    focus_window(0)
