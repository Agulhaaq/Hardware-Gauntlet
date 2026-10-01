"""Unit tests for installer setup wizard and GUI components."""

import os
import tkinter as tk
import pytest
from PIL import Image
from installer.setup_wizard import (
    create_smooth_pill_img,
    locate_hardware_gauntlet_exe,
    PillButton,
    SetupWizard
)


def test_create_smooth_pill_img():
    img = create_smooth_pill_img(100, 30, fill_color="#ffffff", border_color="#333333", scale=2)
    assert isinstance(img, Image.Image)
    assert img.size == (100, 30)
    assert img.mode == "RGBA"


def test_locate_hardware_gauntlet_exe():
    loc = locate_hardware_gauntlet_exe()
    assert loc is None or (isinstance(loc, str) and os.path.exists(loc))


def test_pill_button_widget(tk_session_root):
    frame = tk.Frame(tk_session_root)
    frame.pack()
    try:
        btn = PillButton(frame, text="Test Button", width=120, height=32, is_primary=True)
        assert btn.text == "Test Button"
        assert btn.state == tk.NORMAL

        btn.set_text("Updated Text")
        assert btn.text == "Updated Text"

        btn.set_state(tk.DISABLED)
        assert btn.state == tk.DISABLED

        btn.set_state(tk.NORMAL)
        assert btn.state == tk.NORMAL
    finally:
        frame.destroy()


def test_setup_wizard_navigation(tk_session_root):
    win = tk.Toplevel(tk_session_root)
    win.withdraw()
    try:
        wizard = SetupWizard(win)
        # Should initialize on welcome page
        assert len(wizard.container.winfo_children()) > 0

        # Navigate to options page
        wizard.show_options_page()
        assert len(wizard.container.winfo_children()) > 0

        # Navigate back to welcome page
        wizard.show_welcome_page()
        assert len(wizard.container.winfo_children()) > 0
    finally:
        win.destroy()
