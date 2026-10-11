"""Unit tests for hwscan.core.user_settings."""

import os
import json
import tempfile
import pytest
from hwscan.core.user_settings import (
    get_all_settings,
    get_setting,
    set_setting,
    save_all_settings,
    DEFAULT_SETTINGS,
)


def test_user_settings_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg = os.path.join(tmpdir, "channel_config.json")
        settings = get_all_settings(fake_cfg)
        assert settings["theme"] == "dark"
        assert settings["channel"] == "stable"
        assert settings["active_tab"] == "overview"
        assert get_setting("theme", config_path=fake_cfg) == "dark"


def test_user_settings_set_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg = os.path.join(tmpdir, "channel_config.json")
        success = set_setting("theme", "light", config_path=fake_cfg)
        assert success is True
        assert os.path.exists(fake_cfg)
        assert get_setting("theme", config_path=fake_cfg) == "light"

        # Check file contents
        with open(fake_cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["theme"] == "light"
            assert data["channel"] == "stable"


def test_user_settings_save_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg = os.path.join(tmpdir, "channel_config.json")
        success = save_all_settings(
            {"theme": "light", "active_tab": "health", "stress_gpu": True},
            config_path=fake_cfg
        )
        assert success is True
        settings = get_all_settings(fake_cfg)
        assert settings["theme"] == "light"
        assert settings["active_tab"] == "health"
        assert settings["stress_gpu"] is True


def test_ephemeral_mode():
    from hwscan.core.user_settings import (
        set_ephemeral_mode,
        is_ephemeral_mode,
        get_setting,
        set_setting,
        get_all_settings,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg = os.path.join(tmpdir, "ephemeral_cfg.json")
        set_ephemeral_mode(True)
        assert is_ephemeral_mode() is True

        set_setting("theme", "light", config_path=fake_cfg)
        set_setting("window_geometry", "1400x900", config_path=fake_cfg)
        # Verify no file written to disk
        assert not os.path.exists(fake_cfg)

        # Verify in-memory retrieval
        assert get_setting("theme", config_path=fake_cfg) == "light"
        assert get_setting("window_geometry", config_path=fake_cfg) == "1400x900"
        all_s = get_all_settings(config_path=fake_cfg)
        assert all_s["theme"] == "light"

        # Restore normal mode
        set_ephemeral_mode(False)
        assert is_ephemeral_mode() is False


def test_window_geometry_setting():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg = os.path.join(tmpdir, "geom_cfg.json")
        settings = get_all_settings(fake_cfg)
        assert settings.get("window_geometry") == "1180x820"

        set_setting("window_geometry", "1280x800", config_path=fake_cfg)
        assert get_setting("window_geometry", config_path=fake_cfg) == "1280x800"

