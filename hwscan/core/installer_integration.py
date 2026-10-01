"""System Installation and Single-Instance Management for Hardware Gauntlet."""

import os
import sys
import shutil
import tempfile
import subprocess
from typing import Tuple, Optional

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


def get_install_directory() -> str:
    """Return standard Windows LocalAppData install location."""
    if sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(local_app, "Programs", "HardwareGauntlet")
    else:
        return os.path.expanduser("~/.local/share/hardware-gauntlet")


def is_installed() -> bool:
    """Check if Hardware Gauntlet is installed in the standard program directory."""
    install_dir = get_install_directory()
    if sys.platform == "win32":
        exe_path = os.path.join(install_dir, "HardwareGauntlet.exe")
        return os.path.exists(exe_path)
    else:
        bin_path = os.path.join(install_dir, "hwscan")
        return os.path.exists(bin_path)


def install_application() -> Tuple[bool, str]:
    """Install Hardware Gauntlet permanently onto the host computer.
    
    Creates:
    - Program files in %LOCALAPPDATA%\\Programs\\HardwareGauntlet
    - Start Menu shortcut
    - Desktop shortcut
    - User PATH environment entry
    - Windows Settings (Add/Remove Programs) registration
    """
    if sys.platform != "win32":
        return False, "Automated installer currently optimized for Windows systems."

    install_dir = get_install_directory()
    assets_dir = os.path.join(install_dir, "assets")

    try:
        os.makedirs(install_dir, exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)

        # 1. Locate source files
        current_exe = sys.executable
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        source_exe = os.path.join(base_dir, "HardwareGauntlet.exe")
        if getattr(sys, "frozen", False):
            source_exe = current_exe

        target_exe = os.path.join(install_dir, "HardwareGauntlet.exe")

        # Copy main executable if not running directly from target
        if os.path.exists(source_exe) and os.path.abspath(source_exe) != os.path.abspath(target_exe):
            shutil.copy2(source_exe, target_exe)

        # Copy CLI if available
        cli_candidates = [
            os.path.join(base_dir, "dist", "hwscan-windows-x64.exe"),
            os.path.join(base_dir, "hwscan-windows-x64.exe")
        ]
        target_cli = os.path.join(install_dir, "hwscan.exe")
        for c in cli_candidates:
            if os.path.exists(c):
                shutil.copy2(c, target_cli)
                break

        # Copy assets
        for icon_name in ("app.ico", "app.png", "logo_white_48.png", "logo_black_48.png", "logo_white.png", "logo_black.png"):
            src_icon = os.path.join(base_dir, "assets", icon_name)
            if hasattr(sys, "_MEIPASS"):
                bundle_icon = os.path.join(sys._MEIPASS, "assets", icon_name)
                if os.path.exists(bundle_icon):
                    src_icon = bundle_icon
            if os.path.exists(src_icon):
                shutil.copy2(src_icon, os.path.join(assets_dir, icon_name))

        # Copy or generate uninstaller
        uninstall_ps1_path = os.path.join(install_dir, "uninstall.ps1")
        uninstall_src = os.path.join(base_dir, "installer", "uninstall-windows.ps1")
        if os.path.exists(uninstall_src):
            shutil.copy2(uninstall_src, uninstall_ps1_path)
        else:
            with open(uninstall_ps1_path, "w", encoding="utf-8") as f:
                f.write(
                    '$InstallDir = "$env:LOCALAPPDATA\\Programs\\HardwareGauntlet"\n'
                    'Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Hardware Gauntlet.lnk" -ErrorAction SilentlyContinue\n'
                    'Remove-Item ([System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Hardware Gauntlet.lnk")) -ErrorAction SilentlyContinue\n'
                    'Remove-Item "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\HardwareGauntlet" -Recurse -ErrorAction SilentlyContinue\n'
                    'Start-Process powershell.exe -ArgumentList "-NoProfile -Command `Start-Sleep -Seconds 2; Remove-Item -Path \'$InstallDir\' -Recurse -Force`" -WindowStyle Hidden\n'
                )

        # 2. Invoke PowerShell installer script for shortcuts, PATH, and registry
        ps_script = os.path.join(base_dir, "installer", "install-windows.ps1")
        if os.path.exists(ps_script):
            res = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", ps_script, "-NoLaunch"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            if res.returncode != 0:
                # If script failed, fallback to direct python shortcuts/registry
                _apply_windows_shortcuts_and_registry(install_dir, target_exe, assets_dir)
        else:
            _apply_windows_shortcuts_and_registry(install_dir, target_exe, assets_dir)

        return True, f"Hardware Gauntlet installed successfully to:\n{install_dir}"
    except Exception as e:
        return False, f"Installation failed: {str(e)}"


def _apply_windows_shortcuts_and_registry(install_dir: str, target_exe: str, assets_dir: str):
    """Fallback Windows shortcuts and registry installer using PowerShell commands."""
    icon_file = os.path.join(assets_dir, "app.ico")
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Start Menu
    $StartMenu = "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Hardware Gauntlet.lnk"
    $s = $WshShell.CreateShortcut($StartMenu)
    $s.TargetPath = "{target_exe}"
    $s.WorkingDirectory = "{install_dir}"
    $s.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
    if (Test-Path "{icon_file}") {{ $s.IconLocation = "{icon_file},0" }}
    $s.Save()

    # Desktop
    $Desktop = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Hardware Gauntlet.lnk")
    $d = $WshShell.CreateShortcut($Desktop)
    $d.TargetPath = "{target_exe}"
    $d.WorkingDirectory = "{install_dir}"
    $d.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
    if (Test-Path "{icon_file}") {{ $d.IconLocation = "{icon_file},0" }}
    $d.Save()

    # Registry
    $RegKey = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\HardwareGauntlet"
    New-Item -Path $RegKey -Force | Out-Null
    Set-ItemProperty -Path $RegKey -Name "DisplayName" -Value "Hardware Gauntlet"
    Set-ItemProperty -Path $RegKey -Name "DisplayVersion" -Value "1.0.0"
    Set-ItemProperty -Path $RegKey -Name "Publisher" -Value "Hardware Gauntlet Team"
    Set-ItemProperty -Path $RegKey -Name "InstallLocation" -Value "{install_dir}"
    if (Test-Path "{icon_file}") {{ Set-ItemProperty -Path $RegKey -Name "DisplayIcon" -Value "{icon_file}" }}
    Set-ItemProperty -Path $RegKey -Name "UninstallString" -Value 'powershell.exe -ExecutionPolicy Bypass -NoProfile -File "{install_dir}\\uninstall.ps1"'

    # User PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if ($userPath -notlike "*{install_dir}*") {{
        [Environment]::SetEnvironmentVariable("Path", "$userPath;{install_dir}", [EnvironmentVariableTarget]::User)
    }}
    """
    subprocess.run(
        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", ps_cmd],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    )


def uninstall_application() -> Tuple[bool, str]:
    """Uninstall Hardware Gauntlet from the host computer."""
    install_dir = get_install_directory()
    uninstall_ps1 = os.path.join(install_dir, "uninstall.ps1")
    if os.path.exists(uninstall_ps1):
        try:
            subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", uninstall_ps1],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            return True, "Hardware Gauntlet has been uninstalled."
        except Exception as e:
            return False, f"Uninstall failed: {str(e)}"
    return False, "Uninstaller not found."
