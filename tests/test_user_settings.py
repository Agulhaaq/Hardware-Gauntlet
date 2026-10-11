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
