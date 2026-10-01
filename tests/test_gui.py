"""Unit tests for UI components and theme system in hwscan.gui."""

import tkinter as tk
import pytest
from PIL import Image
from hwscan.gui import (
    THEMES,
    create_smooth_pill_img,
    PillButton,
    RadialDialWidget,
    PillToggle,
    TelemetryWaveCanvas,
    BubbleCapsuleStrip,
    HardwareGauntletGUI
)


def test_themes_structure():
    assert "dark" in THEMES
    assert "light" in THEMES
    required_keys = ["bg", "surface", "card", "text", "accent", "btn_bg", "border"]
    for theme_name, theme in THEMES.items():
        for key in required_keys:
            assert key in theme, f"Missing key '{key}' in theme '{theme_name}'"


def test_create_smooth_pill_img():
    img = create_smooth_pill_img(80, 28, fill_color="#ffffff", border_color="#333333", scale=2)
    assert isinstance(img, Image.Image)
    assert img.size == (80, 28)
    assert img.mode == "RGBA"


def test_gui_pill_button_component(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        btn = PillButton(frame, text="SCAN", width=100, height=32, is_primary=True)
        assert btn.text == "SCAN"
        assert btn.is_primary

        th = THEMES["dark"]
        btn.set_theme(
            bg_parent=th["bg"],
            fill_primary=th["accent"],
            text_primary=th["accent_text"],
            fill_secondary=th["btn_bg"],
            text_secondary=th["btn_fg"],
            border_color=th["btn_border"]
        )

        btn.set_text("PAUSE")
        assert btn.text == "PAUSE"

        btn.set_state(tk.DISABLED)
        assert btn.state == tk.DISABLED

        btn.set_state(tk.NORMAL)
        assert btn.state == tk.NORMAL
    finally:
        frame.destroy()


def test_gui_radial_dial_widget(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        dial = RadialDialWidget(frame, size=160, title="HEALTH SCORE", value_str="95", percent=95.0)
        assert dial.value_str == "95"
        assert dial.percent == 95.0

        dial.update_value("100", 100.0, sub_str="PERFECT", unit="%")
        assert dial.value_str == "100"
        assert dial.sub_str == "PERFECT"
        assert dial.percent == 100.0

        th = THEMES["dark"]
        dial.set_theme(
            bg=th["dial_bg"],
            active_color=th["dial_active"],
            inactive_color=th["dial_inactive"],
            text_color=th["text"],
            dim_color=th["text_dim"]
        )
    finally:
        frame.destroy()


def test_gui_pill_toggle(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        toggled_state = []
        toggle = PillToggle(frame, initial=False, on_toggle=lambda state: toggled_state.append(state))
        assert not toggle.is_on

        # Simulate click
        toggle._on_click(None)
        assert toggle.is_on
        assert toggled_state == [True]

        th = THEMES["dark"]
        toggle.set_theme(
            bg_parent=th["card"],
            pill_bg_off=th["pill_bg_off"],
            pill_border_off=th["pill_border_off"],
            pill_bg_on=th["pill_bg_on"],
            knob_on=th["pill_knob_on"],
            knob_off=th["pill_knob_off"]
        )
    finally:
        frame.destroy()


def test_gui_telemetry_wave(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        wave = TelemetryWaveCanvas(frame, width=200, height=40)
        assert wave.w == 200
        assert wave.h == 40
        wave.set_theme(bg="#15151a", wave_color="#ffffff")
    finally:
        frame.destroy()


def test_gui_bubble_capsule_strip(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        strip_state = []
        strip = BubbleCapsuleStrip(
            frame,
            icon="⚡",
            title="ROOM LAMP",
            desc="Control Lighting Unit",
            initial=True,
            on_toggle=lambda s: strip_state.append(s)
        )
        assert strip.is_on
        assert strip.title == "ROOM LAMP"

        strip._on_click(None)
        assert not strip.is_on
        assert strip_state == [False]
    finally:
        frame.destroy()


def test_hardware_gauntlet_gui_instance():
    app = HardwareGauntletGUI()
    assert app.current_theme == "dark"
    assert app.engine is not None
    assert app.stress_engine is not None
