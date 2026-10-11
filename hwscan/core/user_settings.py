"""Hardware Gauntlet - Portable User Settings Engine.

Persists non-sensitive UI and operational preferences (theme, active tab,
stress-testing toggles) cleanly in channel_config.json without registry bloat.
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
}


def get_all_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve all stored user preferences merged with defaults."""
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
    """Persist a preference key-value pair to channel_config.json."""
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
    cfg_file = get_config_path(config_path)
    try:
        current = get_all_settings(config_path)
        current.update(settings)
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return True
    except Exception:
        return False
