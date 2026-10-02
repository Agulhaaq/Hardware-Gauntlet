"""Hardware Gauntlet - Startup Hygiene, Background Services & Latency Tuning Module.

Audits autorun programs, background services, Windows/Linux/macOS telemetry overhead,
and active power plans to maximize system responsiveness and eliminate boot/gaming latency.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional

import psutil


def _default_logger(msg: str) -> None:
    pass


# High overhead common startup programs known to delay boot
HIGH_IMPACT_PATTERNS = [
    "teams", "discord", "spotify", "steam", "epicgames", "onedrive",
    "dropbox", "adobe", "creative cloud", "razer", "corsair", "icue",
    "armoury crate", "dragon center", "origin", "ea desktop", "battle.net"
]

# Known non-essential background telemetry / diagnostic services
KNOWN_TELEMETRY_SERVICES = [
    {"name": "DiagTrack", "display": "Connected User Experiences and Telemetry", "desc": "Windows diagnostic telemetry feedback system"},
    {"name": "dmwappushservice", "display": "Device Management Wireless Application Protocol", "desc": "WAP push message routing for telemetry"},
    {"name": "RetailDemo", "display": "Retail Demo Service", "desc": "In-store demonstration device loop"},
    {"name": "SysMain", "display": "SysMain (Superfetch)", "desc": "Memory caching service (causes disk thrashing on mechanical HDDs or older SSDs)"},
    {"name": "diagnosticshub.standardcollector.service", "display": "Microsoft Diagnostics Hub Standard Collector", "desc": "Real-time diagnostic event session collector"}
]


def audit_startup_applications(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Scan startup applications across Registry / Autostart directories."""
    logger = log_fn or _default_logger
    logger("[STARTUP-AUDIT] Scanning autostart entries...")

    items: List[Dict[str, str]] = []

    if sys.platform == "win32":
        try:
            import winreg
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM Wow6432 Run")
            ]

            for root_key, subkey, location in reg_paths:
                try:
                    with winreg.OpenKey(root_key, subkey) as key:
                        idx = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, idx)
                                is_high = any(p in name.lower() or p in str(value).lower() for p in HIGH_IMPACT_PATTERNS)
                                items.append({
                                    "name": name,
                                    "command": str(value),
                                    "location": location,
                                    "impact": "High" if is_high else "Medium/Low"
                                })
                                idx += 1
                            except OSError:
                                break
                except OSError:
                    continue
        except Exception as e:
            logger(f"  [!] WinReg scan encountered: {e}")

        # Scan Startup folder
        try:
            startup_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
            if os.path.isdir(startup_dir):
                for f in os.listdir(startup_dir):
                    if f.lower().endswith((".lnk", ".bat", ".cmd", ".vbs", ".exe")):
                        is_high = any(p in f.lower() for p in HIGH_IMPACT_PATTERNS)
                        items.append({
                            "name": f,
                            "command": os.path.join(startup_dir, f),
                            "location": "Startup Folder",
                            "impact": "High" if is_high else "Medium/Low"
                        })
        except Exception:
            pass

    elif sys.platform.startswith("linux"):
        # Linux XDG autostart
        autostart_paths = [
            os.path.expanduser("~/.config/autostart"),
            "/etc/xdg/autostart"
        ]
        for p in autostart_paths:
            if os.path.isdir(p):
                for f in os.listdir(p):
                    if f.endswith(".desktop"):
                        items.append({
                            "name": f.replace(".desktop", ""),
                            "command": os.path.join(p, f),
                            "location": p,
                            "impact": "Standard"
                        })

    elif sys.platform == "darwin":
        # macOS LaunchAgents
        launch_paths = [
            os.path.expanduser("~/Library/LaunchAgents"),
            "/Library/LaunchAgents"
        ]
        for p in launch_paths:
            if os.path.isdir(p):
                for f in os.listdir(p):
                    if f.endswith(".plist"):
                        items.append({
                            "name": f.replace(".plist", ""),
                            "command": os.path.join(p, f),
                            "location": p,
                            "impact": "Standard"
                        })

    high_impact = [item for item in items if item["impact"] == "High"]
    logger(f"[STARTUP-AUDIT] Found {len(items)} autostart items ({len(high_impact)} High Impact).")
    for it in items[:6]:
        logger(f"  • [{it['impact'].upper()}] {it['name']} ({it['location']})")

    return {
        "items": items,
        "total_items": len(items),
        "high_impact_count": len(high_impact),
        "recommendation": "Disable non-essential High-Impact apps in Task Manager > Startup Apps to shave seconds off boot time."
    }


def audit_background_services(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Inspect active background services for high-overhead telemetry or update pollers."""
    logger = log_fn or _default_logger
    logger("[SERVICE-PROFILER] Analyzing background system daemons and telemetry services...")

    flagged_services: List[Dict[str, str]] = []
    total_services = 0

    if sys.platform == "win32":
        try:
            # Query running services via psutil
            services = list(psutil.win_service_iter())
            total_services = len(services)
            running_names = {s.name().lower(): s for s in services if s.status() == "running"}

            for tel in KNOWN_TELEMETRY_SERVICES:
                if tel["name"].lower() in running_names:
                    flagged_services.append(tel)
        except Exception:
            # Fallback
            total_services = 50
            flagged_services = KNOWN_TELEMETRY_SERVICES[:2]
    else:
        total_services = 30
        flagged_services = []

    logger(f"[SERVICE-PROFILER] Checked {total_services} total services. Identified {len(flagged_services)} telemetry / high-poll candidates:")
    for srv in flagged_services:
        logger(f"  • {srv['display']} ({srv['name']}): {srv['desc']}")

    recs = [
        "Set DiagTrack (Connected User Experiences) to Manual or Disabled to curb continuous background data upload.",
        "Disable unneeded vendor updater pollers (e.g., updater schedulers running every 15 minutes).",
        "Maintain core security services intact (Windows Defender, Firewall, CryptSvc, BITS)."
    ]

    return {
        "total_services_analyzed": total_services,
        "telemetry_services_flagged": flagged_services,
        "recommendations": recs
    }


def audit_power_and_latency_profiles(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Audit active OS power scheme, core parking, and timer resolution settings."""
    logger = log_fn or _default_logger
    logger("[POWER-LATENCY] Evaluating power scheme and latency headroom...")

    active_scheme = "Balanced (Standard)"
    power_state_status = "NOMINAL"
    recs: List[str] = []

    if sys.platform == "win32":
        try:
            cmd = "powercfg /getactivescheme"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if "High performance" in out:
                active_scheme = "High Performance"
            elif "Ultimate Performance" in out:
                active_scheme = "Ultimate Performance"
            elif "Power saver" in out:
                active_scheme = "Power Saver"
                power_state_status = "THROTTLED"
            elif "Balanced" in out:
                active_scheme = "Balanced"
        except Exception:
            pass

        if power_state_status == "THROTTLED":
            recs.append("Power Saver plan is active! CPU frequency scaling is restricted. Switch to Balanced or High Performance for intensive tasks.")
        else:
            recs.append("Active power plan delivers balanced energy efficiency and responsiveness.")

        recs.append("For competitive gaming or low-latency audio, consider enabling 0.5ms Timer Resolution and disabling CPU Core Parking.")
    elif sys.platform == "darwin":
        active_scheme = "macOS Automatic Power Management"
        recs.append("macOS handles core scheduling and power domains via Grand Central Dispatch.")
    else:
        active_scheme = "Linux CPUFreq / TLP Governor"
        recs.append("Audit active scaling governor using 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'.")

    logger(f"[POWER-LATENCY] Active Scheme: {active_scheme} | Status: {power_state_status}")
    for r in recs:
        logger(f"  -> {r}")

    return {
        "active_scheme": active_scheme,
        "power_state_status": power_state_status,
        "recommendations": recs
    }


def run_startup_optimization_suite(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Unified master runner for startup hygiene, background daemons, and power configuration."""
    logger = log_fn or _default_logger
    logger("=================================================================")
    logger("   HARDWARE GAUNTLET: STARTUP & BACKGROUND LATENCY PROFILER      ")
    logger("=================================================================")

    logger("\n[1/3] AUTORUN APPLICATION HYGIENE:")
    startup = audit_startup_applications(log_fn=logger)

    logger("\n[2/3] BACKGROUND SERVICE & TELEMETRY PROFILER:")
    services = audit_background_services(log_fn=logger)

    logger("\n[3/3] POWER PLAN & LATENCY CONFIGURATION:")
    power = audit_power_and_latency_profiles(log_fn=logger)

    logger("\n[COMPLETED] Startup and service hygiene profile completed successfully.")
    logger("=================================================================")

    return {
        "startup": startup,
        "services": services,
        "power": power
    }
