"""Single-Instance Mutex and Process Management for Standalone Portable Hardware Gauntlet.

Ensures that only 1 instance of Hardware Gauntlet runs at a time, restoring and
bringing an existing window to the foreground if launched repeatedly.
"""

import os
import sys
import tempfile
from typing import Optional

WINDOW_TITLE = "Hardware Gauntlet - Hardware Diagnostic Suite"
_MUTEX_HANDLE = None


def find_existing_window(window_title: str = WINDOW_TITLE) -> Optional[int]:
    """Search for an existing active Hardware Gauntlet main GUI window."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            # 1. Direct window title match
            hwnd = user32.FindWindowW(None, window_title)
            if hwnd:
                return hwnd

            # 2. Substring match fallback via EnumWindows
            found_hwnds = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def _enum_proc(h, _):
                length = user32.GetWindowTextLengthW(h)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buff, length + 1)
                    title = buff.value
                    if "Hardware Gauntlet" in title and "Launcher" not in title and "Setup" not in title:
                        found_hwnds.append(h)
                        return False
                return True

            user32.EnumWindows(WNDENUMPROC(_enum_proc), 0)
            if found_hwnds:
                return found_hwnds[0]
        except Exception:
            pass
    return None


def focus_window(hwnd: int) -> None:
    """Restore and bring a window to the foreground."""
    if sys.platform == "win32" and hwnd:
        try:
            import ctypes
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            SW_RESTORE = 9
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


def release_single_instance_lock() -> None:
    """Release and close the single-instance mutex handle if held."""
    global _MUTEX_HANDLE
    if sys.platform == "win32" and _MUTEX_HANDLE:
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle(_MUTEX_HANDLE)
        except Exception:
            pass
        _MUTEX_HANDLE = None


def acquire_single_instance_lock(window_title: str = WINDOW_TITLE) -> bool:
    """Ensure strictly 1 instance of Hardware Gauntlet runs.
    
    If another instance is already running:
    - Finds the existing instance's window
    - Restores it from minimized state if necessary
    - Brings it to the foreground
    - Returns False so the new process can terminate cleanly.
    """
    global _MUTEX_HANDLE
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            mutex_name = "Local\\HardwareGauntlet_SingleInstance_Mutex_v1"
            _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, mutex_name)
            last_error = kernel32.GetLastError()
            ERROR_ALREADY_EXISTS = 183

            if last_error == ERROR_ALREADY_EXISTS:
                # Find and focus existing window
                hwnd = find_existing_window(window_title)
                if hwnd:
                    focus_window(hwnd)
                return False
            return True
        except Exception:
            return True
    else:
        # Non-Windows lockfile with fcntl
        lock_file = os.path.join(tempfile.gettempdir(), "hardware_gauntlet_instance.lock")
        try:
            import fcntl
            _MUTEX_HANDLE = open(lock_file, "w")
            fcntl.flock(_MUTEX_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except Exception:
            return False
