"""Hardware Gauntlet - Portable User Settings Engine.

Persists non-sensitive UI and operational preferences (theme, active tab,
stress-testing toggles, window geometry) cleanly in channel_config.json
without registry bloat. Supports in-memory ephemeral mode for pure zero-write runs.
"""

import os
import json
from typing import Any, Dict, Optional
from hwscan.core.update_channel import get_config_path

DEFAULT_SETTINGS: Dict[str, Any] = {
    "channel": "stable",
    "theme": "dark",
    "active_tab": "overview",
    "stress_gpu": False,
    "stress_duration": 30,
    "window_geometry": "1180x820",
}

_EPHEMERAL_MODE: bool = False
_EPHEMERAL_STORE: Dict[str, Any] = {}


def set_ephemeral_mode(enabled: bool = True) -> None:
    """Toggle ephemeral (in-memory only, zero disk writes) mode."""
    global _EPHEMERAL_MODE
    _EPHEMERAL_MODE = enabled
    if enabled and not _EPHEMERAL_STORE:
        _EPHEMERAL_STORE.update(DEFAULT_SETTINGS)


def is_ephemeral_mode() -> bool:
    """Return whether ephemeral mode is active."""
    return _EPHEMERAL_MODE


def get_all_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve all stored user preferences merged with defaults."""
    if _EPHEMERAL_MODE:
        settings = dict(DEFAULT_SETTINGS)
        settings.update(_EPHEMERAL_STORE)
        return settings

    cfg_file = get_config_path(config_path)
    settings = dict(DEFAULT_SETTINGS)
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass
    return settings


def get_setting(key: str, default: Any = None, config_path: Optional[str] = None) -> Any:
    """Retrieve an individual preference value."""
    settings = get_all_settings(config_path)
    fallback = DEFAULT_SETTINGS.get(key, default)
    return settings.get(key, fallback)


def set_setting(key: str, value: Any, config_path: Optional[str] = None) -> bool:
    """Persist a preference key-value pair to channel_config.json or memory if ephemeral."""
    if _EPHEMERAL_MODE:
        _EPHEMERAL_STORE[key] = value
        return True

    cfg_file = get_config_path(config_path)
    try:
        data = get_all_settings(config_path)
        data[key] = value
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def save_all_settings(settings: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """Persist multiple preference values in a single transaction."""
    if _EPHEMERAL_MODE:
        _EPHEMERAL_STORE.update(settings)
        return True

    cfg_file = get_config_path(config_path)
    try:
        current = get_all_settings(config_path)
        current.update(settings)
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return True
    except Exception:
        return False
