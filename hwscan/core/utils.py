"""Utility helpers for Hardware Gauntlet."""

import os
import sys
import platform
import subprocess
import shutil
from typing import Optional, List, Union


def run_command(cmd: Union[str, List[str]], timeout: int = 10, shell: Optional[bool] = None) -> str:
    """Run a system command safely and return standard output as stripped string."""
    if shell is None:
        shell = isinstance(cmd, str)

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        return proc.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, PermissionError):
        return ""


def run_powershell_json(script: str, timeout: int = 15) -> str:
    """Execute a PowerShell command returning JSON."""
    if sys.platform != "win32":
        return ""
    full_cmd = f"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command \"{script} | ConvertTo-Json -Depth 4 -Compress\""
    return run_command(full_cmd, timeout=timeout, shell=True)


def format_bytes(bytes_value: Optional[Union[int, float]]) -> str:
    """Format bytes into human readable format (GB, MB, etc.)."""
    if bytes_value is None or bytes_value < 0:
        return "N/A"
    
    value = float(bytes_value)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if value < 1024.0:
            if unit in ['B', 'KB']:
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} EB"


def format_hz(mhz_or_hz: Optional[Union[int, float]], is_mhz: bool = True) -> str:
    """Format clock speed in MHz or Hz into GHz / MHz."""
    if not mhz_or_hz or mhz_or_hz <= 0:
        return "N/A"
    
    mhz = float(mhz_or_hz) if is_mhz else float(mhz_or_hz) / 1_000_000.0
    if mhz >= 1000.0:
        return f"{mhz / 1000.0:.2f} GHz"
    return f"{int(mhz)} MHz"


def format_uptime(seconds: Optional[Union[int, float]]) -> str:
    """Format seconds into days, hours, minutes."""
    if seconds is None or seconds < 0:
        return "Unknown"
    
    sec = int(seconds)
    days = sec // 86400
    hours = (sec % 86400) // 3600
    minutes = (sec % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "< 1m"


def is_admin() -> bool:
    """Check if the current process has administrative / root privileges."""
    try:
        if sys.platform == "win32":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            return os.geteuid() == 0  # type: ignore
    except Exception:
        return False


def get_current_os() -> str:
    """Return standard lowercase OS identifier: 'windows', 'macos', 'linux', or 'other'."""
    p = platform.system().lower()
    if p == "darwin":
        return "macos"
    if p == "windows":
        return "windows"
    if p == "linux":
        return "linux"
    return p
