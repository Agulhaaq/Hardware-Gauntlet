"""Native Desktop GUI Application for Hardware Gauntlet with Ultra-Smooth Anti-Aliased 100Days Aesthetic.

Engineered with:
- Retina-grade supersampled (Lanczos) anti-aliased radial dials (matching 26°C thermostat)
- Smooth anti-aliased capsule pill buttons (PillButton) with zero polygon distortion
- Smooth animated sliding pill toggle switches (PillToggle)
- High-framerate tear-free in-place telemetry wave spline (TelemetryWaveCanvas)
- Minimalist duotone monochrome styling (Obsidian & crisp Slate)
- Single-instance mutex enforcement & manual scan execution
"""

import os
import sys
import json
import time
import math
import subprocess
import webbrowser
import threading
from typing import Optional, Dict, Any, Callable, List, Tuple

from PIL import Image, ImageDraw, ImageTk

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.core.utils import format_bytes, format_hz
from hwscan.core.stress_test import StressTestEngine
from hwscan.core.installer_integration import (
    acquire_single_instance_lock,
    install_application,
    uninstall_application,
    is_installed,
    get_install_directory,
    WINDOW_TITLE
)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog


THEMES = {
    "dark": {
        "name": "dark",
        "bg": "#08080a",
        "surface": "#101014",
        "card": "#15151a",
        "card_alt": "#1c1c22",
        "border": "#25252e",
        "border_subtle": "#1a1a20",
        "border_light": "#363644",
        "text": "#ffffff",
        "text_dim": "#a1a1aa",
        "text_muted": "#71717a",
        "accent": "#ffffff",
        "accent_text": "#08080a",
        "accent_hover": "#e4e4e7",
        "btn_bg": "#1c1c22",
        "btn_fg": "#ffffff",
        "btn_border": "#2a2a34",
        "btn_hover": "#262630",
        "pill_bg_off": "#202026",
        "pill_border_off": "#343440",
        "pill_bg_on": "#ffffff",
        "pill_knob_on": "#08080a",
        "pill_knob_off": "#8e8e98",
        "dial_bg": "#15151a",
        "dial_active": (255, 255, 255, 255),
        "dial_inactive": (38, 38, 48, 255),
        "wave_color": "#ffffff",
        "console_bg": "#0c0c0e",
        "console_fg": "#e4e4e7",
        "tree_bg": "#101014",
        "tree_fg": "#ffffff",
        "tree_alt": "#131318",
        "tree_head_bg": "#17171d",
        "tree_head_fg": "#ffffff",
        "tree_sel_bg": "#25252e",
        "tree_sel_fg": "#ffffff",
        "tab_bg": "#17171d",
        "tab_fg": "#a1a1aa",
        "tab_sel_bg": "#ffffff",
        "tab_sel_fg": "#08080a",
        "capsule_bg": "#121217",
        "capsule_border": "#252532",
        "toggle_text": "☀️ LIGHT MODE",
        "logo_file": "logo_white_48.png",
        "logo_fallback": "logo_white.png",
    },
    "light": {
        "name": "light",
        "bg": "#f5f5f7",
        "surface": "#ffffff",
        "card": "#ffffff",
        "card_alt": "#f0f0f4",
        "border": "#e5e5ea",
        "border_subtle": "#ededf2",
        "border_light": "#d1d1d6",
        "text": "#09090b",
        "text_dim": "#64748b",
        "text_muted": "#94a3b8",
        "accent": "#09090b",
        "accent_text": "#ffffff",
        "accent_hover": "#27272a",
        "btn_bg": "#ffffff",
        "btn_fg": "#0f172a",
        "btn_border": "#e2e8f0",
        "btn_hover": "#f1f5f9",
        "pill_bg_off": "#e5e5ea",
        "pill_border_off": "#d1d1d6",
        "pill_bg_on": "#09090b",
        "pill_knob_on": "#ffffff",
        "pill_knob_off": "#8e8e93",
        "capsule_bg": "#f9f9fb",
        "capsule_border": "#e2e8f0",
        "dial_bg": "#ffffff",
        "dial_active": (9, 9, 11, 255),
        "dial_inactive": (226, 232, 240, 255),
        "wave_color": "#09090b",
        "console_bg": "#f8fafc",
        "console_fg": "#0f172a",
        "tree_bg": "#ffffff",
        "tree_fg": "#09090b",
        "tree_alt": "#f8fafc",
        "tree_head_bg": "#f1f5f9",
        "tree_head_fg": "#0f172a",
        "tree_sel_bg": "#e2e8f0",
        "tree_sel_fg": "#09090b",
        "tab_bg": "#f1f5f9",
        "tab_fg": "#64748b",
        "tab_sel_bg": "#09090b",
        "tab_sel_fg": "#ffffff",
        "toggle_text": "🌙 DARK MODE",
        "logo_file": "logo_black_48.png",
        "logo_fallback": "logo_black.png",
    }
}


def get_asset_file_path(filename: str) -> str:
    """Resolve asset paths whether running from source, PyInstaller bundle, or installed directory."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "assets", filename))
        candidates.append(os.path.join(sys._MEIPASS, filename))
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "assets", filename))
    candidates.append(os.path.join(exe_dir, filename))
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(repo_root, "assets", filename))
    candidates.append(os.path.join(repo_root, filename))
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        candidates.append(os.path.join(appdata, "Programs", "HardwareGauntlet", "assets", filename))

    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(repo_root, "assets", filename)


def create_smooth_pill_img(w: int, h: int, fill_color: str, border_color: Optional[str] = None, scale: int = 2) -> Image.Image:
    """Render a pixel-perfect, anti-aliased pill capsule with Lanczos downsampling."""
    ws = w * scale
    hs = h * scale
    rad = hs / 2.0
    im = Image.new("RGBA", (ws, hs), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, ws - 2, hs - 2], radius=rad, fill=fill_color, outline=border_color, width=scale if border_color else 0)
    return im.resize((w, h), Image.Resampling.LANCZOS)


class PillButton(tk.Canvas):
    """Ultra-smooth anti-aliased capsule pill button using supersampled PIL textures."""

    def __init__(self, parent, text="BUTTON", command=None, width=120, height=32, is_primary=True, font=("Segoe UI", 8, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, cursor="hand2", **kwargs)
        self.text = text
        self.command = command
        self.w = width
        self.h = height
        self.is_primary = is_primary
        self.btn_font = font
        self.state = tk.NORMAL

        self.bg_parent = "#101014"
        self.fill_color = "#ffffff" if is_primary else "#1c1c22"
        self.text_color = "#08080a" if is_primary else "#ffffff"
        self.hover_color = "#e4e4e7" if is_primary else "#262630"
        self.border_color = "#ffffff" if is_primary else "#2a2a34"
        self._is_hovered = False

        self._img_norm: Optional[ImageTk.PhotoImage] = None
        self._img_hover: Optional[ImageTk.PhotoImage] = None
        self._img_disabled: Optional[ImageTk.PhotoImage] = None

        self._bg_img_id = None
        self._text_id = None

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._bake_images()
        self.draw()

    def set_theme(self, bg_parent: str, fill_primary: str, text_primary: str, fill_secondary: str, text_secondary: str, border_color: str):
        self.bg_parent = bg_parent
        self.configure(bg=bg_parent)
        if self.is_primary:
            self.fill_color = fill_primary
            self.text_color = text_primary
            self.hover_color = "#e4e4e7" if fill_primary == "#ffffff" else "#27272a"
            self.border_color = fill_primary
        else:
            self.fill_color = fill_secondary
            self.text_color = text_secondary
            self.hover_color = "#282832" if fill_secondary == "#1c1c22" else "#f1f5f9"
            self.border_color = border_color
        self._bake_images()
        self.draw()

    def _bake_images(self):
        norm_raw = create_smooth_pill_img(self.w, self.h, self.fill_color, self.border_color if not self.is_primary else None)
        self._img_norm = ImageTk.PhotoImage(norm_raw)

        hover_raw = create_smooth_pill_img(self.w, self.h, self.hover_color, self.border_color if not self.is_primary else None)
        self._img_hover = ImageTk.PhotoImage(hover_raw)

        dis_raw = create_smooth_pill_img(self.w, self.h, "#22222a" if not self.is_primary else "#3f3f46", None)
        self._img_disabled = ImageTk.PhotoImage(dis_raw)

    def set_text(self, new_text: str):
        self.text = new_text
        if self._text_id:
            self.itemconfig(self._text_id, text=new_text)

    def set_state(self, state: str):
        self.state = state
        self.configure(cursor="hand2" if state == tk.NORMAL else "arrow")
        self.draw()

    def _on_enter(self, e):
        if self.state == tk.NORMAL:
            self._is_hovered = True
            self.draw()

    def _on_leave(self, e):
        self._is_hovered = False
        self.draw()

    def _on_click(self, e):
        if self.state == tk.NORMAL and self.command:
            self.command()

    def draw(self):
        self.delete("all")
        if self.state == tk.DISABLED:
            img = self._img_disabled
            t_col = "#71717a"
        elif self._is_hovered:
            img = self._img_hover
            t_col = self.text_color
        else:
            img = self._img_norm
            t_col = self.text_color

        self._bg_img_id = self.create_image(0, 0, anchor="nw", image=img)
        self._text_id = self.create_text(self.w / 2.0, self.h / 2.0, text=self.text, fill=t_col, font=self.btn_font)


class RadialDialWidget(tk.Canvas):
    """Retina-grade supersampled (Lanczos) circular radial tick dial matching 26°C thermostat."""

    def __init__(self, parent, size: int = 176, title: str = "GAUGE", value_str: str = "--", unit: str = "", sub_str: str = "READY", percent: float = 0.0, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self.size = size
        self.title_text = title
        self.value_str = value_str
        self.unit = unit
        self.sub_str = sub_str
        self.percent = percent

        self.bg_color = "#15151a"
        self.dial_active = (255, 255, 255, 255)
        self.dial_inactive = (38, 38, 48, 255)
        self.text_color = "#ffffff"
        self.dim_color = "#a1a1aa"

        self._bg_img_id = None
        self._val_text_id = None
        self._sub_text_id = None
        self._title_text_id = None
        self._current_photo = None
        self._last_rendered_pct = -1.0

        self.draw()

    def set_theme(self, bg: str, active_color: Tuple[int, int, int, int], inactive_color: Tuple[int, int, int, int], text_color: str, dim_color: str):
        self.bg_color = bg
        self.dial_active = active_color
        self.dial_inactive = inactive_color
        self.text_color = text_color
        self.dim_color = dim_color
        self.configure(bg=bg)
        self._last_rendered_pct = -1.0
        self.draw()

    def update_value(self, value_str: str, percent: float = 0.0, sub_str: str = "", unit: str = None):
        self.value_str = value_str
        self.percent = max(0.0, min(100.0, percent))
        if sub_str:
            self.sub_str = sub_str
        if unit is not None:
            self.unit = unit
        self.draw()

    def draw(self):
        # 1. Re-render smooth ticks image with Pillow 2x supersampling if percentage changed
        scale = 2
        w_s = self.size * scale
        h_s = self.size * scale

        # Only recompute dial bitmap if percentage changed or theme invalidated
        pct_key = round(self.percent, 1)
        if pct_key != self._last_rendered_pct:
            self._last_rendered_pct = pct_key

            # Background color tuple
            bg_rgb = self.winfo_rgb(self.bg_color)
            bg_tuple = (bg_rgb[0] >> 8, bg_rgb[1] >> 8, bg_rgb[2] >> 8, 255)

            img = Image.new("RGBA", (w_s, h_s), bg_tuple)
            draw = ImageDraw.Draw(img)

            cx = w_s / 2.0
            cy = h_s / 2.0
            radius = (w_s / 2.0) - (24 * scale)
            inner_radius = radius - (14 * scale)

            start_angle = 135.0
            sweep_angle = 270.0
            num_ticks = 42

            active_count = int(round((self.percent / 100.0) * num_ticks))

            for i in range(num_ticks):
                frac = i / float(num_ticks - 1)
                deg = start_angle + frac * sweep_angle
                rad = math.radians(deg)

                x1 = cx + (inner_radius * math.cos(rad))
                y1 = cy + (inner_radius * math.sin(rad))
                x2 = cx + (radius * math.cos(rad))
                y2 = cy + (radius * math.sin(rad))

                col = self.dial_active if (i <= active_count and active_count > 0) else self.dial_inactive
                line_w = int(round(3.5 * scale)) if (i <= active_count and active_count > 0) else int(round(2.2 * scale))
                draw.line([(x1, y1), (x2, y2)], fill=col, width=line_w)

            # High-grade Lanczos downscale for silky smooth anti-aliased lines
            smooth_img = img.resize((self.size, self.size), Image.Resampling.LANCZOS)
            self._current_photo = ImageTk.PhotoImage(smooth_img)

        # 2. Update Canvas image and text objects
        self.delete("all")
        cx = self.size / 2.0
        cy = self.size / 2.0

        if self._current_photo:
            self.create_image(0, 0, anchor="nw", image=self._current_photo)

        display_val = f"{self.value_str}{self.unit}"
        val_font_size = 20 if len(display_val) <= 4 else 15
        self.create_text(cx, cy - 8, text=display_val, fill=self.text_color, font=("Segoe UI", val_font_size, "bold"))
        self.create_text(cx, cy + 16, text=self.sub_str.upper(), fill=self.dim_color, font=("Segoe UI", 7, "bold"))
        self.create_text(cx, self.size - 22, text=self.title_text.upper(), fill=self.dim_color, font=("Segoe UI", 7, "bold"))


class PillToggle(tk.Canvas):
    """Ultra-smooth anti-aliased capsule pill toggle with sliding animation."""

    def __init__(self, parent, initial: bool = True, on_toggle: Optional[Callable[[bool], None]] = None, **kwargs):
        super().__init__(parent, width=46, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        self.is_on = initial
        self.on_toggle = on_toggle
        self.bg_parent = "#15151a"

        self.pill_bg_off = "#202026"
        self.pill_border_off = "#343440"
        self.pill_bg_on = "#ffffff"
        self.pill_knob_on = "#08080a"
        self.pill_knob_off = "#8e8e98"

        self._current_knob_x = 25.0 if initial else 3.0
        self._target_knob_x = 25.0 if initial else 3.0
        self._animating = False

        self._track_on_img = None
        self._track_off_img = None
        self._knob_on_img = None
        self._knob_off_img = None

        self.bind("<Button-1>", self._on_click)
        self._bake_textures()
        self.draw()

    def set_theme(self, bg_parent: str, pill_bg_off: str, pill_border_off: str, pill_bg_on: str, knob_on: str, knob_off: str):
        self.bg_parent = bg_parent
        self.pill_bg_off = pill_bg_off
        self.pill_border_off = pill_border_off
        self.pill_bg_on = pill_bg_on
        self.pill_knob_on = knob_on
        self.pill_knob_off = knob_off
        self.configure(bg=bg_parent)
        self._bake_textures()
        self.draw()

    def _bake_textures(self):
        scale = 2
        w, h = 46, 24
        ws, hs = w * scale, h * scale

        # Track ON
        t_on = Image.new("RGBA", (ws, hs), (0, 0, 0, 0))
        d_on = ImageDraw.Draw(t_on)
        d_on.rounded_rectangle([1, 1, ws - 2, hs - 2], radius=hs / 2.0, fill=self.pill_bg_on)
        self._track_on_img = ImageTk.PhotoImage(t_on.resize((w, h), Image.Resampling.LANCZOS))

        # Track OFF
        t_off = Image.new("RGBA", (ws, hs), (0, 0, 0, 0))
        d_off = ImageDraw.Draw(t_off)
        d_off.rounded_rectangle([1, 1, ws - 2, hs - 2], radius=hs / 2.0, fill=self.pill_bg_off, outline=self.pill_border_off, width=scale)
        self._track_off_img = ImageTk.PhotoImage(t_off.resize((w, h), Image.Resampling.LANCZOS))

        # Knob ON
        ks = 18 * scale
        k_on = Image.new("RGBA", (ks, ks), (0, 0, 0, 0))
        dk_on = ImageDraw.Draw(k_on)
        dk_on.ellipse([1, 1, ks - 2, ks - 2], fill=self.pill_knob_on)
        self._knob_on_img = ImageTk.PhotoImage(k_on.resize((18, 18), Image.Resampling.LANCZOS))

        # Knob OFF
        k_off = Image.new("RGBA", (ks, ks), (0, 0, 0, 0))
        dk_off = ImageDraw.Draw(k_off)
        dk_off.ellipse([1, 1, ks - 2, ks - 2], fill=self.pill_knob_off)
        self._knob_off_img = ImageTk.PhotoImage(k_off.resize((18, 18), Image.Resampling.LANCZOS))

    def _on_click(self, event):
        self.is_on = not self.is_on
        self._target_knob_x = 25.0 if self.is_on else 3.0
        self._start_animation()
        if self.on_toggle:
            self.on_toggle(self.is_on)

    def _start_animation(self):
        if not self._animating:
            self._animating = True
            self._animate_step()

    def _animate_step(self):
        dx = self._target_knob_x - self._current_knob_x
        if abs(dx) <= 2.0:
            self._current_knob_x = self._target_knob_x
            self._animating = False
            self.draw()
        else:
            self._current_knob_x += dx * 0.45
            self.draw()
            self.after(16, self._animate_step)

    def draw(self):
        self.delete("all")
        track_img = self._track_on_img if self.is_on else self._track_off_img
        knob_img = self._knob_on_img if self.is_on else self._knob_off_img

        if track_img:
            self.create_image(0, 0, anchor="nw", image=track_img)
        if knob_img:
            self.create_image(int(round(self._current_knob_x)), 3, anchor="nw", image=knob_img)


class TelemetryWaveCanvas(tk.Canvas):
    """Silky-smooth, tear-free 30fps in-place coords animated telemetry wave."""

    def __init__(self, parent, width=300, height=52, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.phase = 0.0
        self.wave_color = "#ffffff"
        self.bg_color = "#15151a"
        self.line_id = self.create_line([0, height / 2.0, width, height / 2.0], fill=self.wave_color, width=2, smooth=True)
        self._animate()

    def set_theme(self, bg: str, wave_color: str):
        self.bg_color = bg
        self.wave_color = wave_color
        self.configure(bg=bg)
        self.itemconfig(self.line_id, fill=wave_color)

    def _animate(self):
        if not self.winfo_exists():
            return
        self.phase += 0.065
        mid_y = self.h / 2.0
        amp1 = 12.0
        amp2 = 5.5

        pts = []
        for x in range(6, self.w - 6, 4):
            y = mid_y + amp1 * math.sin((x * 0.036) + self.phase) + amp2 * math.cos((x * 0.082) - self.phase * 0.4)
            pts.extend([x, y])

        if len(pts) >= 4:
            self.coords(self.line_id, *pts)

        self.after(33, self._animate)  # Smooth 30 FPS tear-free


class BubbleCapsuleStrip(tk.Canvas):
    """Floating bubble capsule control strip matching the 'ROOM LAMP' / 'ROOM OUTLET' design in 100Days."""

    def __init__(self, parent, icon: str, title: str, desc: str, initial: bool = True, on_toggle: Optional[Callable[[bool], None]] = None, height: int = 54, **kwargs):
        super().__init__(parent, height=height, highlightthickness=0, cursor="hand2", **kwargs)
        self.w = 380
        self.h = height
        self.icon = icon
        self.title = title
        self.desc = desc
        self.is_on = initial
        self.on_toggle = on_toggle

        self.bg_parent = "#15151a"
        self.capsule_bg = "#121217"
        self.capsule_border = "#252532"
        self.text_color = "#ffffff"
        self.dim_color = "#a1a1aa"

        self.pill_bg_off = "#202026"
        self.pill_border_off = "#343440"
        self.pill_bg_on = "#ffffff"
        self.pill_knob_on = "#08080a"
        self.pill_knob_off = "#8e8e98"

        self.track_w = 46
        self.track_h = 24
        self.track_x = self.w - self.track_w - 18
        self.track_y = (self.h - self.track_h) / 2.0

        self._knob_min_x = self.track_x + 3.0
        self._knob_max_x = self.track_x + 25.0
        self._current_knob_x = self._knob_max_x if initial else self._knob_min_x
        self._target_knob_x = self._knob_max_x if initial else self._knob_min_x
        self._animating = False

        self._bg_img: Optional[ImageTk.PhotoImage] = None
        self._track_on_img: Optional[ImageTk.PhotoImage] = None
        self._track_off_img: Optional[ImageTk.PhotoImage] = None
        self._knob_on_img: Optional[ImageTk.PhotoImage] = None
        self._knob_off_img: Optional[ImageTk.PhotoImage] = None

        self.bind("<Configure>", self._on_configure)
        self.bind("<Button-1>", self._on_click)
        self._bake_all()
        self.draw()

    def _on_configure(self, e):
        if e.width > 60 and e.width != self.w:
            self.w = e.width
            self.track_x = self.w - self.track_w - 18
            self._knob_min_x = self.track_x + 3.0
            self._knob_max_x = self.track_x + 25.0
            self._current_knob_x = self._knob_max_x if self.is_on else self._knob_min_x
            self._target_knob_x = self._knob_max_x if self.is_on else self._knob_min_x
            self._bake_bg()
            self.draw()

    def set_theme(self, bg_parent: str, capsule_bg: str, capsule_border: str, text_color: str, dim_color: str, pill_bg_off: str, pill_border_off: str, pill_bg_on: str, knob_on: str, knob_off: str):
        self.bg_parent = bg_parent
        self.capsule_bg = capsule_bg
        self.capsule_border = capsule_border
        self.text_color = text_color
        self.dim_color = dim_color
        self.pill_bg_off = pill_bg_off
        self.pill_border_off = pill_border_off
        self.pill_bg_on = pill_bg_on
        self.pill_knob_on = knob_on
        self.pill_knob_off = knob_off
        self.configure(bg=bg_parent)
        self._bake_all()
        self.draw()

    def _bake_bg(self):
        scale = 2
        ws = max(10, self.w * scale)
        hs = self.h * scale
        rad = hs / 2.0
        bg_im = Image.new("RGBA", (ws, hs), (0, 0, 0, 0))
        d_bg = ImageDraw.Draw(bg_im)
        d_bg.rounded_rectangle([1, 1, ws - 2, hs - 2], radius=rad, fill=self.capsule_bg, outline=self.capsule_border, width=scale)
        self._bg_img = ImageTk.PhotoImage(bg_im.resize((self.w, self.h), Image.Resampling.LANCZOS))

    def _bake_all(self):
        self._bake_bg()
        scale = 2
        t_ws = self.track_w * scale
        t_hs = self.track_h * scale

        t_on = Image.new("RGBA", (t_ws, t_hs), (0, 0, 0, 0))
        d_on = ImageDraw.Draw(t_on)
        d_on.rounded_rectangle([1, 1, t_ws - 2, t_hs - 2], radius=t_hs / 2.0, fill=self.pill_bg_on)
        self._track_on_img = ImageTk.PhotoImage(t_on.resize((self.track_w, self.track_h), Image.Resampling.LANCZOS))

        t_off = Image.new("RGBA", (t_ws, t_hs), (0, 0, 0, 0))
        d_off = ImageDraw.Draw(t_off)
        d_off.rounded_rectangle([1, 1, t_ws - 2, t_hs - 2], radius=t_hs / 2.0, fill=self.pill_bg_off, outline=self.pill_border_off, width=scale)
        self._track_off_img = ImageTk.PhotoImage(t_off.resize((self.track_w, self.track_h), Image.Resampling.LANCZOS))

        ks = 18 * scale
        k_on = Image.new("RGBA", (ks, ks), (0, 0, 0, 0))
        dk_on = ImageDraw.Draw(k_on)
        dk_on.ellipse([1, 1, ks - 2, ks - 2], fill=self.pill_knob_on)
        self._knob_on_img = ImageTk.PhotoImage(k_on.resize((18, 18), Image.Resampling.LANCZOS))

        k_off = Image.new("RGBA", (ks, ks), (0, 0, 0, 0))
        dk_off = ImageDraw.Draw(k_off)
        dk_off.ellipse([1, 1, ks - 2, ks - 2], fill=self.pill_knob_off)
        self._knob_off_img = ImageTk.PhotoImage(k_off.resize((18, 18), Image.Resampling.LANCZOS))

    def _on_click(self, event):
        self.is_on = not self.is_on
        self._target_knob_x = self._knob_max_x if self.is_on else self._knob_min_x
        self._start_animation()
        if self.on_toggle:
            self.on_toggle(self.is_on)

    def _start_animation(self):
        if not self._animating:
            self._animating = True
            self._animate_step()

    def _animate_step(self):
        dx = self._target_knob_x - self._current_knob_x
        if abs(dx) <= 1.5:
            self._current_knob_x = self._target_knob_x
            self._animating = False
            self.draw()
        else:
            self._current_knob_x += dx * 0.45
            self.draw()
            self.after(16, self._animate_step)

    def draw(self):
        self.delete("all")
        if self._bg_img:
            self.create_image(0, 0, anchor="nw", image=self._bg_img)

        self.create_text(28, self.h / 2.0, text=self.icon, font=("Segoe UI Emoji", 13), anchor="center")

        status_text = "ACTIVE" if self.is_on else "STANDBY"
        self.create_text(54, self.h / 2.0 - 9, text=self.title.upper(), fill=self.text_color, font=("Segoe UI", 9, "bold"), anchor="w")
        self.create_text(54, self.h / 2.0 + 9, text=f"{status_text} • {self.desc}", fill=self.dim_color, font=("Segoe UI", 7), anchor="w")

        track_img = self._track_on_img if self.is_on else self._track_off_img
        knob_img = self._knob_on_img if self.is_on else self._knob_off_img
        if track_img:
            self.create_image(self.track_x, self.track_y, anchor="nw", image=track_img)
        if knob_img:
            self.create_image(int(round(self._current_knob_x)), self.track_y + 3, anchor="nw", image=knob_img)


class HardwareGauntletGUI:
    """Orchestrates modern desktop application with 100Days design aesthetic."""

    def __init__(self):
        self.engine = HardwareScannerEngine()
        self.stress_engine = StressTestEngine()
        self.html_reporter = HTMLReporter()
        self.json_reporter = JSONReporter()
        self.current_report = None
        self.current_theme = "dark"
        self._is_scanning = False

    def run(self, prefer_engine: str = "auto") -> None:
        """Launch the native desktop application window with single-instance lock."""
        if not acquire_single_instance_lock(WINDOW_TITLE):
            print("[*] Another instance of Hardware Gauntlet is already running. Focus transferred to active window.")
            return

        self._run_tkinter()

    def _run_tkinter(self) -> None:
        """Render native Tkinter GUI with duotone design, radial dials, and pill buttons."""
        root = tk.Tk()
        root.title(WINDOW_TITLE)
        root.geometry("1180x820")
        root.minsize(980, 700)

        ico_path = get_asset_file_path("app.ico")
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                root.iconbitmap(ico_path)
            except Exception:
                pass

        themed_widgets = {
            "root_bg": [root],
            "surface": [],
            "cards": [],
            "card_alts": [],
            "borders": [],
            "text_primary": [],
            "text_dim": [],
            "text_muted": [],
            "pill_buttons": [],
            "consoles": [],
            "treeviews": [],
            "dials": [],
            "waves": [],
            "pill_toggles": [],
            "capsule_strips": []
        }

        style = ttk.Style()
        style.theme_use("clam")

        # -------------------------------------------------------------
        # Header Toolbar (Clean Monochrome + Pill Buttons)
        # -------------------------------------------------------------
        header = tk.Frame(root, padx=24, pady=16, highlightthickness=1)
        header.pack(fill=tk.X, side=tk.TOP)
        themed_widgets["surface"].append(header)
        themed_widgets["borders"].append(header)

        title_box = tk.Frame(header)
        title_box.pack(side=tk.LEFT)
        themed_widgets["surface"].append(title_box)

        lbl_logo = tk.Label(title_box)
        lbl_logo.pack(side=tk.LEFT, padx=(0, 14))
        themed_widgets["surface"].append(lbl_logo)

        title_text_box = tk.Frame(title_box)
        title_text_box.pack(side=tk.LEFT)
        themed_widgets["surface"].append(title_text_box)

        title_row = tk.Frame(title_text_box)
        title_row.pack(anchor="w")
        themed_widgets["surface"].append(title_row)

        lbl_main_title = tk.Label(title_row, text="YOUR SYSTEM — HARDWARE GAUNTLET", font=("Segoe UI", 13, "bold"))
        lbl_main_title.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_main_title)
        themed_widgets["text_primary"].append(lbl_main_title)

        lbl_tag = tk.Label(title_row, text="v1.0.0 • Pure Local", font=("Segoe UI", 8, "bold"), padx=6, pady=1)
        lbl_tag.pack(side=tk.LEFT, padx=(10, 0))
        themed_widgets["card_alts"].append(lbl_tag)
        themed_widgets["text_dim"].append(lbl_tag)

        lbl_subtitle = tk.Label(title_text_box, text="System Standby — Click '▶ RUN FULL SCAN' to audit hardware parameters.", font=("Segoe UI", 9))
        lbl_subtitle.pack(anchor="w", pady=(2, 0))
        themed_widgets["surface"].append(lbl_subtitle)
        themed_widgets["text_dim"].append(lbl_subtitle)

        # Header Action Pill Buttons
        btn_frame = tk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        themed_widgets["surface"].append(btn_frame)

        def do_scan():
            if self._is_scanning:
                return
            self._is_scanning = True
            btn_scan.set_state(tk.DISABLED)
            btn_scan.set_text("⏳ SCANNING...")
            btn_overview_scan.set_state(tk.DISABLED)
            btn_overview_scan.set_text("⏳ SCANNING...")
            dial_health.update_value("...", 35.0, "AUDITING")
            lbl_subtitle.config(text="Auditing processor architecture, DIMM memory modules, GPU, storage arrays, and UEFI security...")
            threading.Thread(target=run_background_scan, daemon=True).start()

        def do_export_html():
            if not self.current_report:
                messagebox.showinfo("Scan Required", "Please run a hardware scan first before exporting an HTML report.")
                return
            f = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Diagnostic Report", "*.html")],
                initialfile=f"hardware-report-{self.current_report.system.hostname}.html"
            )
            if f:
                self.html_reporter.write_file(self.current_report, f)
                if messagebox.askyesno("Report Saved", f"Offline HTML report saved successfully to:\n{f}\n\nWould you like to open it now?"):
                    webbrowser.open(f)

        def do_export_json():
            if not self.current_report:
                messagebox.showinfo("Scan Required", "Please run a hardware scan first before exporting JSON data.")
                return
            f = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Hardware Data", "*.json")],
                initialfile=f"hardware-report-{self.current_report.system.hostname}.json"
            )
            if f:
                self.json_reporter.write_file(self.current_report, f)
                messagebox.showinfo("JSON Saved", f"Machine-readable JSON report saved to:\n{f}")

        def do_install():
            btn_install.set_state(tk.DISABLED)
            btn_install.set_text("⏳ INSTALLING...")
            def worker():
                success, msg = install_application()
                def on_done():
                    btn_install.set_state(tk.NORMAL)
                    btn_install.set_text("✓ INSTALLED" if success else "📦 INSTALL TO PC")
                    if success:
                        lbl_install_status.config(text=f"Status: Installed at {get_install_directory()}")
                        messagebox.showinfo("Installation Complete", f"{msg}\n\n• Start Menu shortcut created\n• Desktop shortcut created\n• CLI command 'hwscan' added to PATH\n• Visible in Windows Settings > Installed Apps")
                    else:
                        messagebox.showerror("Installation Error", msg)
                root.after(0, on_done)
            threading.Thread(target=worker, daemon=True).start()

        def toggle_theme():
            self.current_theme = "light" if self.current_theme == "dark" else "dark"
            apply_current_theme()

        def launch_os_tool(tool_cmd):
            try:
                subprocess.Popen(tool_cmd, shell=True)
            except Exception as err:
                messagebox.showerror("Tool Error", f"Unable to launch {tool_cmd}:\n{err}")

        # Pill Buttons in Header
        btn_scan = PillButton(btn_frame, text="▶ RUN SCAN", command=do_scan, width=116, height=32, is_primary=True)
        btn_scan.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_scan)

        btn_install = PillButton(btn_frame, text="✓ INSTALLED" if is_installed() else "📦 INSTALL", command=do_install, width=108, height=32, is_primary=False)
        btn_install.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_install)

        btn_theme = PillButton(btn_frame, text="☀️ LIGHT", command=toggle_theme, width=96, height=32, is_primary=False)
        btn_theme.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_theme)

        btn_html = PillButton(btn_frame, text="📄 HTML", command=do_export_html, width=82, height=32, is_primary=False)
        btn_html.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_html)

        btn_json = PillButton(btn_frame, text="💾 JSON", command=do_export_json, width=78, height=32, is_primary=False)
        btn_json.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_json)

        # -------------------------------------------------------------
        # Bubble Capsule Tab Navigation (Pure 100Days Pill Bar)
        # -------------------------------------------------------------
        tab_bar = tk.Frame(root, padx=24, pady=8)
        tab_bar.pack(fill=tk.X, side=tk.TOP, pady=(10, 0))
        themed_widgets["root_bg"].append(tab_bar)

        pages_container = tk.Frame(root, padx=24, pady=8)
        pages_container.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        themed_widgets["root_bg"].append(pages_container)

        tab_definitions = [
            ("📊 OVERVIEW", 112),
            ("🔥 STRESS TEST", 120),
            ("🧠 CPU & BOARD", 122),
            ("💾 MEMORY", 102),
            ("🎮 GRAPHICS", 108),
            ("💽 STORAGE", 104),
            ("🔒 SECURITY", 104),
            ("🛠️ UTILITIES", 106),
        ]

        tab_pages = []
        tab_pills = []
        active_tab_idx = [0]

        def switch_tab(target_idx: int):
            active_tab_idx[0] = target_idx
            for i, page in enumerate(tab_pages):
                if i == target_idx:
                    page.pack(fill=tk.BOTH, expand=True)
                else:
                    page.pack_forget()

            th = THEMES[self.current_theme]
            for i, pill in enumerate(tab_pills):
                pill.is_primary = (i == target_idx)
                pill.set_theme(
                    bg_parent=th["bg"],
                    fill_primary=th["accent"],
                    text_primary=th["accent_text"],
                    fill_secondary=th["btn_bg"],
                    text_secondary=th["btn_fg"],
                    border_color=th["btn_border"]
                )

        for idx, (title, width) in enumerate(tab_definitions):
            page_frame = tk.Frame(pages_container)
            tab_pages.append(page_frame)
            themed_widgets["root_bg"].append(page_frame)

            pill = PillButton(tab_bar, text=title, command=lambda i=idx: switch_tab(i), width=width, height=32, is_primary=(idx == 0))
            pill.pack(side=tk.LEFT, padx=3)
            tab_pills.append(pill)
            themed_widgets["pill_buttons"].append(pill)

        tab_overview = tab_pages[0]
        tab_stress = tab_pages[1]
        tab_cpu = tab_pages[2]
        tab_mem = tab_pages[3]
        tab_gpu = tab_pages[4]
        tab_storage = tab_pages[5]
        tab_security = tab_pages[6]
        tab_tools = tab_pages[7]

        # Initially display overview
        tab_overview.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # Tab 1: Overview with Thermostat Dial & Telemetry Wave
        # -------------------------------------------------------------
        overview_top = tk.Frame(tab_overview)
        overview_top.pack(fill=tk.X, pady=(0, 14))
        themed_widgets["root_bg"].append(overview_top)

        # Featured Card 01: Thermostat Radial Dial for Health Score
        card_dial = tk.Frame(overview_top, width=280, padx=20, pady=16, highlightthickness=1)
        card_dial.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        themed_widgets["cards"].append(card_dial)
        themed_widgets["borders"].append(card_dial)

        lbl_dial_card_title = tk.Label(card_dial, text="CARD 01 — SYSTEM HEALTH", font=("Segoe UI", 9, "bold"))
        lbl_dial_card_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_dial_card_title)
        themed_widgets["text_primary"].append(lbl_dial_card_title)

        lbl_dial_card_sub = tk.Label(card_dial, text="Real-time hardware integrity rating", font=("Segoe UI", 8))
        lbl_dial_card_sub.pack(anchor="w", pady=(1, 10))
        themed_widgets["cards"].append(lbl_dial_card_sub)
        themed_widgets["text_dim"].append(lbl_dial_card_sub)

        dial_health = RadialDialWidget(card_dial, size=180, title="HEALTH SCORE", value_str="--", sub_str="READY", percent=0.0)
        dial_health.pack(pady=4)
        themed_widgets["dials"].append((dial_health, "cards"))

        # Underneath dial: Two pill buttons side by side matching [ POWER ] and [ MODE ]
        dial_btn_row = tk.Frame(card_dial)
        dial_btn_row.pack(fill=tk.X, pady=(12, 0))
        themed_widgets["cards"].append(dial_btn_row)

        btn_overview_scan = PillButton(dial_btn_row, text="▶ RUN SCAN", command=do_scan, width=108, height=32, is_primary=True)
        btn_overview_scan.pack(side=tk.LEFT, padx=(0, 4))
        themed_widgets["pill_buttons"].append(btn_overview_scan)

        btn_overview_export = PillButton(dial_btn_row, text="📄 REPORT", command=do_export_html, width=108, height=32, is_primary=False)
        btn_overview_export.pack(side=tk.LEFT, padx=(4, 0))
        themed_widgets["pill_buttons"].append(btn_overview_export)

        # Right Column: Telemetry Waveform Card + 4 Metric Cards
        overview_right = tk.Frame(overview_top)
        overview_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        themed_widgets["root_bg"].append(overview_right)

        # Waveform card (matching upper right card in 100Days design)
        card_wave = tk.Frame(overview_right, padx=18, pady=12, highlightthickness=1)
        card_wave.pack(fill=tk.X, pady=(0, 10))
        themed_widgets["cards"].append(card_wave)
        themed_widgets["borders"].append(card_wave)

        wave_header = tk.Frame(card_wave)
        wave_header.pack(fill=tk.X)
        themed_widgets["cards"].append(wave_header)

        lbl_wave_title = tk.Label(wave_header, text="YOUR SYSTEM — REAL-TIME TELEMETRY", font=("Segoe UI", 9, "bold"))
        lbl_wave_title.pack(side=tk.LEFT)
        themed_widgets["cards"].append(lbl_wave_title)
        themed_widgets["text_primary"].append(lbl_wave_title)

        wave_canvas = TelemetryWaveCanvas(card_wave, width=540, height=48)
        wave_canvas.pack(fill=tk.X, pady=(4, 4))
        themed_widgets["waves"].append(wave_canvas)

        lbl_wave_sub = tk.Label(card_wave, text="Continuous hardware pulse — All buses verified nominal", font=("Segoe UI", 8))
        lbl_wave_sub.pack(anchor="w")
        themed_widgets["cards"].append(lbl_wave_sub)
        themed_widgets["text_dim"].append(lbl_wave_sub)

        # 4 System Metric Cards in 2x2 Grid
        overview_cards_grid = tk.Frame(overview_right)
        overview_cards_grid.pack(fill=tk.BOTH, expand=True)
        themed_widgets["root_bg"].append(overview_cards_grid)

        def create_metric_card(parent, card_num, title, row, col):
            card = tk.Frame(parent, padx=16, pady=10, highlightthickness=1)
            card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
            themed_widgets["cards"].append(card)
            themed_widgets["borders"].append(card)

            lbl_hdr = tk.Label(card, text=f"{card_num} — {title.upper()}", font=("Segoe UI", 8, "bold"))
            lbl_hdr.pack(anchor="w")
            themed_widgets["cards"].append(lbl_hdr)
            themed_widgets["text_dim"].append(lbl_hdr)

            lbl_v = tk.Label(card, text="Click '▶ RUN SCAN'", font=("Segoe UI", 11, "bold"))
            lbl_v.pack(anchor="w", pady=(3, 1))
            themed_widgets["cards"].append(lbl_v)
            themed_widgets["text_primary"].append(lbl_v)

            lbl_s = tk.Label(card, text="Awaiting trigger", font=("Segoe UI", 8))
            lbl_s.pack(anchor="w")
            themed_widgets["cards"].append(lbl_s)
            themed_widgets["text_dim"].append(lbl_s)
            return lbl_v, lbl_s

        overview_cards_grid.columnconfigure(0, weight=1)
        overview_cards_grid.columnconfigure(1, weight=1)
        overview_cards_grid.rowconfigure(0, weight=1)
        overview_cards_grid.rowconfigure(1, weight=1)

        kpi_cpu_v, kpi_cpu_s = create_metric_card(overview_cards_grid, "CARD 02", "Processor Architecture", 0, 0)
        kpi_mem_v, kpi_mem_s = create_metric_card(overview_cards_grid, "CARD 03", "Memory DIMM Topology", 0, 1)
        kpi_gpu_v, kpi_gpu_s = create_metric_card(overview_cards_grid, "CARD 04", "Graphics Accelerator", 1, 0)
        kpi_sec_v, kpi_sec_s = create_metric_card(overview_cards_grid, "CARD 05", "Firmware & Security", 1, 1)

        # Bottom Findings Treeview
        lbl_findings_hdr = tk.Label(tab_overview, text="HARDWARE AUDIT FINDINGS & ALERTS —", font=("Segoe UI", 10, "bold"))
        lbl_findings_hdr.pack(anchor="w", pady=(4, 6))
        themed_widgets["root_bg"].append(lbl_findings_hdr)
        themed_widgets["text_primary"].append(lbl_findings_hdr)

        tree_warn = ttk.Treeview(tab_overview, columns=("level", "category", "details"), show="headings", height=8)
        tree_warn.heading("level", text="Severity")
        tree_warn.heading("category", text="Category")
        tree_warn.heading("details", text="Observation & Recommendation")
        tree_warn.column("level", width=110, anchor="center")
        tree_warn.column("category", width=140)
        tree_warn.column("details", width=760)
        tree_warn.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_warn)
        tree_warn.insert("", tk.END, values=("READY", "Scanner", "System audit ready. Click '▶ RUN FULL SCAN' in the toolbar to begin analysis."), tags=("even",))

        # -------------------------------------------------------------
        # Tab 2: 🔥 Stress Test with Dual Thermostat Dials & Pill Toggles
        # -------------------------------------------------------------
        stress_top = tk.Frame(tab_stress)
        stress_top.pack(fill=tk.X, pady=(0, 12))
        themed_widgets["root_bg"].append(stress_top)

        # Dial 1: Thermal Dial (matching exact 26°C thermostat from image)
        card_thermal_dial = tk.Frame(stress_top, width=240, padx=16, pady=14, highlightthickness=1)
        card_thermal_dial.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        themed_widgets["cards"].append(card_thermal_dial)
        themed_widgets["borders"].append(card_thermal_dial)

        lbl_td_title = tk.Label(card_thermal_dial, text="THERMAL DIAL —", font=("Segoe UI", 9, "bold"))
        lbl_td_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_td_title)
        themed_widgets["text_primary"].append(lbl_td_title)

        dial_thermal = RadialDialWidget(card_thermal_dial, size=160, title="TEMP", value_str="--", unit="°C", sub_str="IDLE", percent=0.0)
        dial_thermal.pack(pady=4)
        themed_widgets["dials"].append((dial_thermal, "cards"))

        # Dial 2: CPU Torture Dial
        card_cpu_dial = tk.Frame(stress_top, width=240, padx=16, pady=14, highlightthickness=1)
        card_cpu_dial.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        themed_widgets["cards"].append(card_cpu_dial)
        themed_widgets["borders"].append(card_cpu_dial)

        lbl_cd_title = tk.Label(card_cpu_dial, text="CPU TORTURE —", font=("Segoe UI", 9, "bold"))
        lbl_cd_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_cd_title)
        themed_widgets["text_primary"].append(lbl_cd_title)

        dial_cpu = RadialDialWidget(card_cpu_dial, size=160, title="LOAD", value_str="0.0", unit="%", sub_str="READY", percent=0.0)
        dial_cpu.pack(pady=4)
        themed_widgets["dials"].append((dial_cpu, "cards"))

        # Controls & Bubble Capsule Switches Card (matching 'ROOM LAMP', 'ROOM OUTLET' design)
        card_controls = tk.Frame(stress_top, padx=22, pady=16, highlightthickness=1)
        card_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        themed_widgets["cards"].append(card_controls)
        themed_widgets["borders"].append(card_controls)

        lbl_ctrl_title = tk.Label(card_controls, text="SUBSYSTEM BENCHMARK CONTROLS ——", font=("Segoe UI", 9, "bold"))
        lbl_ctrl_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_ctrl_title)
        themed_widgets["text_primary"].append(lbl_ctrl_title)

        lbl_ctrl_desc = tk.Label(card_controls, text="Toggle targeted hardware pipelines for torture benchmarking", font=("Segoe UI", 8))
        lbl_ctrl_desc.pack(anchor="w", pady=(1, 12))
        themed_widgets["cards"].append(lbl_ctrl_desc)
        themed_widgets["text_dim"].append(lbl_ctrl_desc)

        # 3 Floating Bubble Capsule Strips
        strip_cpu = BubbleCapsuleStrip(card_controls, icon="🧠", title="CPU Multi-Core Torture", desc="Math, trigonometry & SHA-256 on all logical cores", initial=True)
        strip_cpu.pack(fill=tk.X, pady=(0, 6))
        themed_widgets["capsule_strips"].append(strip_cpu)

        strip_ram = BubbleCapsuleStrip(card_controls, icon="💾", title="RAM Bit-Flip Integrity", desc="1GB alternating pattern buffers (0xAA, 0x55)", initial=True)
        strip_ram.pack(fill=tk.X, pady=(0, 6))
        themed_widgets["capsule_strips"].append(strip_ram)

        strip_disk = BubbleCapsuleStrip(card_controls, icon="💽", title="Disk Sequential I/O", desc="Sequential write and read speed benchmark", initial=True)
        strip_disk.pack(fill=tk.X, pady=(0, 10))
        themed_widgets["capsule_strips"].append(strip_disk)

        # Duration & Pill Execution buttons
        stress_act_row = tk.Frame(card_controls)
        stress_act_row.pack(fill=tk.X, pady=(4, 0))
        themed_widgets["cards"].append(stress_act_row)

        lbl_dur = tk.Label(stress_act_row, text="DURATION:", font=("Segoe UI", 8, "bold"))
        lbl_dur.pack(side=tk.LEFT, padx=(2, 8))
        themed_widgets["cards"].append(lbl_dur)
        themed_widgets["text_dim"].append(lbl_dur)

        combo_duration = ttk.Combobox(stress_act_row, values=["15s (Quick Check)", "30s (Standard Run)", "60s (Heavy Torture)", "120s (Burn-in)"], state="readonly", width=18)
        combo_duration.current(1)
        combo_duration.pack(side=tk.LEFT, padx=(0, 12))

        # Pill buttons for stress start and stop
        btn_start_stress = PillButton(stress_act_row, text="▶ START TORTURE", width=132, height=32, is_primary=True)
        btn_start_stress.pack(side=tk.LEFT, padx=(0, 6))
        themed_widgets["pill_buttons"].append(btn_start_stress)

        btn_stop_stress = PillButton(stress_act_row, text="⏹ STOP", width=78, height=32, is_primary=False)
        btn_stop_stress.pack(side=tk.LEFT)
        btn_stop_stress.set_state(tk.DISABLED)
        themed_widgets["pill_buttons"].append(btn_stop_stress)

        # Progress bar
        stress_progress_frame = tk.Frame(tab_stress)
        stress_progress_frame.pack(fill=tk.X, pady=(0, 8))
        themed_widgets["root_bg"].append(stress_progress_frame)

        stress_progress = ttk.Progressbar(stress_progress_frame, mode="determinate", length=600)
        stress_progress.pack(fill=tk.X)

        lbl_stress_status = tk.Label(stress_progress_frame, text="Status: Ready to benchmark. Select duration and click '▶ START TORTURE'.", font=("Segoe UI", 9))
        lbl_stress_status.pack(anchor="w", pady=(3, 0))
        themed_widgets["root_bg"].append(lbl_stress_status)
        themed_widgets["text_dim"].append(lbl_stress_status)

        # Bottom Split: Live Diagnostics Console & Windows Benchmarks
        stress_bottom = tk.Frame(tab_stress)
        stress_bottom.pack(fill=tk.BOTH, expand=True)
        themed_widgets["root_bg"].append(stress_bottom)

        console_frame = tk.Frame(stress_bottom, highlightthickness=1)
        console_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        themed_widgets["surface"].append(console_frame)
        themed_widgets["borders"].append(console_frame)

        console_title_bar = tk.Frame(console_frame, padx=12, pady=6)
        console_title_bar.pack(fill=tk.X)
        themed_widgets["surface"].append(console_title_bar)

        lbl_console_title = tk.Label(console_title_bar, text="REAL-TIME DIAGNOSTIC CONSOLE —", font=("Segoe UI", 8, "bold"))
        lbl_console_title.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_console_title)
        themed_widgets["text_dim"].append(lbl_console_title)

        txt_console = tk.Text(console_frame, font=("Consolas", 9), relief=tk.FLAT, padx=12, pady=8, height=8)
        txt_console.pack(fill=tk.BOTH, expand=True)
        themed_widgets["consoles"].append(txt_console)

        def log_console(msg: str):
            timestamp = time.strftime("%H:%M:%S")
            txt_console.insert(tk.END, f"[{timestamp}] {msg}\n")
            txt_console.see(tk.END)

        log_console("Hardware Gauntlet Torture Engine online.")
        log_console("Multi-core CPU mathematical torture, RAM pattern integrity, and thermal telemetry active.")

        # Windows Benchmarks Box with Pill buttons
        win_tools_box = tk.Frame(stress_bottom, width=280, padx=14, pady=12, highlightthickness=1)
        win_tools_box.pack(side=tk.RIGHT, fill=tk.Y)
        themed_widgets["surface"].append(win_tools_box)
        themed_widgets["borders"].append(win_tools_box)

        lbl_win_bench = tk.Label(win_tools_box, text="WINDOWS BENCHMARKS —", font=("Segoe UI", 9, "bold"))
        lbl_win_bench.pack(anchor="w", pady=(0, 8))
        themed_widgets["surface"].append(lbl_win_bench)
        themed_widgets["text_primary"].append(lbl_win_bench)

        def add_quick_tool(title, cmd):
            f = tk.Frame(win_tools_box, pady=3)
            f.pack(fill=tk.X)
            themed_widgets["surface"].append(f)
            b = PillButton(f, text=title, command=lambda: launch_os_tool(cmd), width=236, height=30, is_primary=False)
            b.pack(fill=tk.X)
            themed_widgets["pill_buttons"].append(b)

        if sys.platform == "win32":
            add_quick_tool("🧠 MEMORY CHECK (mdsched)", "mdsched.exe")
            add_quick_tool("📈 PERF REPORT (perfmon)", "perfmon.exe /report")
            add_quick_tool("⚡ WINSAT BENCHMARK", "winsat.exe formal")
            add_quick_tool("🎮 DIRECTX DIAGNOSTIC", "dxdiag.exe")
        else:
            lbl_other = tk.Label(win_tools_box, text="Platform benchmark utilities available via OS console.", font=("Segoe UI", 8))
            lbl_other.pack(anchor="w")
            themed_widgets["surface"].append(lbl_other)
            themed_widgets["text_dim"].append(lbl_other)

        # Stress Execution logic
        def on_stress_telemetry(t: Dict[str, Any]):
            def update():
                progress = t.get("progress_percent", 0.0)
                stress_progress["value"] = progress

                cpu_pct = t.get("cpu_percent", 0.0)
                freq = t.get("cpu_freq_mhz", 0.0)
                dial_cpu.update_value(f"{cpu_pct:.0f}", cpu_pct, f"{freq/1000:.1f} GHz" if freq > 0 else "ACTIVE")

                gpu_temp = t.get("gpu_temp")
                if gpu_temp is not None:
                    t_pct = min(100.0, (gpu_temp / 100.0) * 100.0)
                    status_str = "NOMINAL" if gpu_temp < 75 else ("WARM" if gpu_temp < 85 else "CRITICAL")
                    dial_thermal.update_value(str(gpu_temp), t_pct, status_str)
                else:
                    dial_thermal.update_value("NORM", progress, "PASS")

                lbl_stress_status.config(text=f"Status: Stress testing in progress... Elapsed: {t.get('elapsed', 0)}s / {t.get('duration', 30)}s ({progress:.0f}%)")
            root.after(0, update)

        def on_stress_complete(summary: Dict[str, Any]):
            def update():
                stress_progress["value"] = 100
                btn_start_stress.set_state(tk.NORMAL)
                btn_stop_stress.set_state(tk.DISABLED)

                verdict = summary.get("stability_status", "PASSED")
                dial_cpu.update_value("0.0", 0.0, "COMPLETE")
                lbl_stress_status.config(text=f"Status: COMPLETED in {summary.get('total_elapsed', 0)}s • Verdict: {verdict}")
                log_console(f"Torture benchmark finished. Verdict: {verdict}")
                log_console(f"Peak CPU Load: {summary.get('peak_cpu_load', 0)}% | Peak GPU Temp: {summary.get('peak_gpu_temp', 'N/A')} °C")
                log_console(f"RAM Integrity Errors: {summary.get('ram_errors', 0)}")
                if summary.get("disk_write_speed", 0) > 0:
                    log_console(f"Disk Sequential Write: {summary.get('disk_write_speed')} MB/s | Read: {summary.get('disk_read_speed')} MB/s")
                messagebox.showinfo("Stress Test Complete", f"Hardware Torture Benchmark Finished!\n\nVerdict: {verdict}\nPeak CPU Load: {summary.get('peak_cpu_load', 0)}%\nPeak GPU Temp: {summary.get('peak_gpu_temp', 'N/A')} °C\nRAM Bit Errors: {summary.get('ram_errors', 0)}")
            root.after(0, update)

        def start_stress():
            duration_map = {0: 15, 1: 30, 2: 60, 3: 120}
            dur = duration_map.get(combo_duration.current(), 30)

            c_on = strip_cpu.is_on
            r_on = strip_ram.is_on
            d_on = strip_disk.is_on

            if not (c_on or r_on or d_on):
                messagebox.showwarning("Selection Required", "Please select at least one subsystem to stress test.")
                return

            btn_start_stress.set_state(tk.DISABLED)
            btn_stop_stress.set_state(tk.NORMAL)
            stress_progress["value"] = 0
            lbl_stress_status.config(text="Status: Launching hardware stress workers...")

            log_console(f"Starting {dur}s stress test [CPU: {c_on}, RAM: {r_on}, Disk: {d_on}]...")
            self.stress_engine.start_test(
                duration_seconds=dur,
                test_cpu=c_on,
                test_ram=r_on,
                test_disk=d_on,
                ram_mb=1024,
                on_telemetry=on_stress_telemetry,
                on_completion=on_stress_complete
            )

        def stop_stress():
            self.stress_engine.stop_test()
            btn_start_stress.set_state(tk.NORMAL)
            btn_stop_stress.set_state(tk.DISABLED)
            lbl_stress_status.config(text="Status: Test stopped by user.")
            log_console("Stress test aborted by user.")

        btn_start_stress.command = start_stress
        btn_stop_stress.command = stop_stress

        # -------------------------------------------------------------
        # Tab 3: CPU & Motherboard
        # -------------------------------------------------------------
        tree_cpu = ttk.Treeview(tab_cpu, columns=("prop", "val"), show="headings")
        tree_cpu.heading("prop", text="Hardware Specification")
        tree_cpu.heading("val", text="Observed Value")
        tree_cpu.column("prop", width=280)
        tree_cpu.column("val", width=760)
        tree_cpu.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_cpu)

        # -------------------------------------------------------------
        # Tab 4: RAM & DIMMs
        # -------------------------------------------------------------
        tree_mem = ttk.Treeview(tab_mem, columns=("slot", "cap", "type", "speed", "mfg", "part"), show="headings")
        tree_mem.heading("slot", text="DIMM Slot / Bank")
        tree_mem.heading("cap", text="Module Capacity")
        tree_mem.heading("type", text="Memory Gen")
        tree_mem.heading("speed", text="Clock Speed")
        tree_mem.heading("mfg", text="Manufacturer")
        tree_mem.heading("part", text="Module Part Number")
        for col in ("slot", "cap", "type", "speed", "mfg", "part"):
            tree_mem.column(col, width=160)
        tree_mem.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_mem)

        # -------------------------------------------------------------
        # Tab 5: GPU & Displays
        # -------------------------------------------------------------
        tree_gpu = ttk.Treeview(tab_gpu, columns=("name", "vendor", "vram", "driver", "res"), show="headings")
        tree_gpu.heading("name", text="Graphics Accelerator")
        tree_gpu.heading("vendor", text="Vendor")
        tree_gpu.heading("vram", text="Dedicated VRAM")
        tree_gpu.heading("driver", text="Driver Version")
        tree_gpu.heading("res", text="Resolution & Refresh")
        tree_gpu.column("name", width=280)
        tree_gpu.column("vendor", width=120)
        tree_gpu.column("vram", width=140)
        tree_gpu.column("driver", width=160)
        tree_gpu.column("res", width=200)
        tree_gpu.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_gpu)

        # -------------------------------------------------------------
        # Tab 6: Storage & Partitions
        # -------------------------------------------------------------
        tree_storage = ttk.Treeview(tab_storage, columns=("mount", "fs", "total", "used", "free", "percent"), show="headings")
        tree_storage.heading("mount", text="Drive / Physical Mount")
        tree_storage.heading("fs", text="Filesystem / Type")
        tree_storage.heading("total", text="Total Capacity")
        tree_storage.heading("used", text="Used Space")
        tree_storage.heading("free", text="Free Space")
        tree_storage.heading("percent", text="Utilization")
        for col in ("mount", "fs", "total", "used", "free", "percent"):
            tree_storage.column(col, width=150)
        tree_storage.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_storage)

        # -------------------------------------------------------------
        # Tab 7: Security & Network
        # -------------------------------------------------------------
        tree_sec = ttk.Treeview(tab_security, columns=("component", "status", "details"), show="headings")
        tree_sec.heading("component", text="Security Subsystem")
        tree_sec.heading("status", text="Operational State")
        tree_sec.heading("details", text="Technical Cryptographic Details")
        tree_sec.column("component", width=220)
        tree_sec.column("status", width=160)
        tree_sec.column("details", width=620)
        tree_sec.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_sec)

        # -------------------------------------------------------------
        # Tab 8: System Tools, Diagnostics & Installation
        # -------------------------------------------------------------
        lbl_tools_hdr = tk.Label(tab_tools, text="DIRECT OPERATING SYSTEM DIAGNOSTIC SHORTCUTS —", font=("Segoe UI", 11, "bold"))
        lbl_tools_hdr.pack(anchor="w", pady=(0, 14))
        themed_widgets["root_bg"].append(lbl_tools_hdr)
        themed_widgets["text_primary"].append(lbl_tools_hdr)

        tools_grid = tk.Frame(tab_tools)
        tools_grid.pack(fill=tk.X, pady=(0, 16))
        themed_widgets["root_bg"].append(tools_grid)

        def add_tool_card(parent, title, desc, cmd):
            card = tk.Frame(parent, padx=14, pady=14, highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            themed_widgets["surface"].append(card)
            themed_widgets["borders"].append(card)

            t = tk.Label(card, text=title, font=("Segoe UI", 10, "bold"))
            t.pack(anchor="w")
            themed_widgets["surface"].append(t)
            themed_widgets["text_primary"].append(t)

            d = tk.Label(card, text=desc, font=("Segoe UI", 8))
            d.pack(anchor="w", pady=(2, 10))
            themed_widgets["surface"].append(d)
            themed_widgets["text_dim"].append(d)

            b = PillButton(card, text="LAUNCH TOOL", command=lambda: launch_os_tool(cmd), width=180, height=30, is_primary=False)
            b.pack(fill=tk.X)
            themed_widgets["pill_buttons"].append(b)

        if sys.platform == "win32":
            add_tool_card(tools_grid, "🔌 Device Manager", "Hardware drivers & controllers", "devmgmt.msc")
            add_tool_card(tools_grid, "📈 Task Manager", "Real-time thread utilization", "taskmgr.exe")
            add_tool_card(tools_grid, "💾 Disk Management", "Partition layouts & health", "diskmgmt.msc")
            add_tool_card(tools_grid, "ℹ️ System Info", "MSInfo32 firmware tables", "msinfo32.exe")

        # Installation & System Registration Card
        install_card = tk.Frame(tab_tools, padx=20, pady=16, highlightthickness=1)
        install_card.pack(fill=tk.BOTH, expand=True)
        themed_widgets["surface"].append(install_card)
        themed_widgets["borders"].append(install_card)

        lbl_inst_title = tk.Label(install_card, text="CARD 06 — SYSTEM INSTALLATION & SHORTCUT MANAGEMENT", font=("Segoe UI", 11, "bold"))
        lbl_inst_title.pack(anchor="w")
        themed_widgets["surface"].append(lbl_inst_title)
        themed_widgets["text_primary"].append(lbl_inst_title)

        lbl_install_status = tk.Label(
            install_card,
            text=f"Status: {'Installed at ' + get_install_directory() if is_installed() else 'Running in standalone portable mode'}",
            font=("Segoe UI", 9)
        )
        lbl_install_status.pack(anchor="w", pady=(4, 12))
        themed_widgets["surface"].append(lbl_install_status)
        themed_widgets["text_dim"].append(lbl_install_status)

        inst_btn_row = tk.Frame(install_card)
        inst_btn_row.pack(anchor="w", pady=(0, 14))
        themed_widgets["surface"].append(inst_btn_row)

        btn_install_tab = PillButton(inst_btn_row, text="📦 INSTALL TO PC", command=do_install, width=150, height=34, is_primary=True)
        btn_install_tab.pack(side=tk.LEFT, padx=(0, 10))
        themed_widgets["pill_buttons"].append(btn_install_tab)

        def do_open_folder():
            p = get_install_directory() if is_installed() else os.getcwd()
            os.startfile(p) if sys.platform == "win32" else subprocess.Popen(["xdg-open", p])

        btn_folder = PillButton(inst_btn_row, text="📂 OPEN FOLDER", command=do_open_folder, width=130, height=34, is_primary=False)
        btn_folder.pack(side=tk.LEFT, padx=(0, 10))
        themed_widgets["pill_buttons"].append(btn_folder)

        def do_uninstall():
            if messagebox.askyesno("Uninstall", "Are you sure you want to uninstall Hardware Gauntlet from your PC?"):
                success, msg = uninstall_application()
                if success:
                    lbl_install_status.config(text="Status: Uninstalled from PC (Running portable)")
                    btn_install.set_text("📦 INSTALL")
                    messagebox.showinfo("Uninstalled", "Hardware Gauntlet shortcuts and registry entries have been removed.")
                else:
                    messagebox.showerror("Error", msg)

        btn_uninst = PillButton(inst_btn_row, text="🗑️ UNINSTALL", command=do_uninstall, width=110, height=34, is_primary=False)
        btn_uninst.pack(side=tk.LEFT)
        themed_widgets["pill_buttons"].append(btn_uninst)

        info_text = (
            "• Running Mode: Native Offline Client Application (Zero Network / No Localhost Required)\n"
            "• Single Instance Lock: Only 1 application window open at a time (focuses existing instance)\n"
            "• Scanning Architecture: In-Memory Multi-Threaded Telemetry Collector\n"
            "• Torture & Benchmarks: CPU torture, RAM pattern integrity check, disk throughput, thermal monitor\n"
            "• System Registration: Desktop Shortcut, Start Menu, User PATH, and Windows Settings Uninstaller"
        )
        lbl_info_body = tk.Label(install_card, text=info_text, font=("Segoe UI", 9), justify=tk.LEFT)
        lbl_info_body.pack(anchor="w")
        themed_widgets["surface"].append(lbl_info_body)
        themed_widgets["text_dim"].append(lbl_info_body)

        # -------------------------------------------------------------
        # Theme Dispatcher
        # -------------------------------------------------------------
        logo_cache: Dict[str, Any] = {}

        def get_theme_logo(theme_name: str):
            if theme_name in logo_cache:
                return logo_cache[theme_name]
            cfg = THEMES[theme_name]
            p = get_asset_file_path(cfg["logo_file"])
            if not os.path.exists(p):
                p = get_asset_file_path(cfg["logo_fallback"])
            if os.path.exists(p):
                try:
                    img = tk.PhotoImage(file=p)
                    logo_cache[theme_name] = img
                    return img
                except Exception:
                    pass
            return None

        def apply_current_theme():
            th = THEMES[self.current_theme]

            for w in themed_widgets["root_bg"]:
                try:
                    w.config(bg=th["bg"])
                except Exception:
                    pass

            for w in themed_widgets["surface"]:
                try:
                    w.config(bg=th["surface"])
                except Exception:
                    pass

            for w in themed_widgets["cards"]:
                try:
                    w.config(bg=th["card"])
                except Exception:
                    pass

            for w in themed_widgets["card_alts"]:
                try:
                    w.config(bg=th["card_alt"])
                except Exception:
                    pass

            for w in themed_widgets["borders"]:
                try:
                    w.config(highlightbackground=th["border"], highlightcolor=th["border"])
                except Exception:
                    pass

            for w in themed_widgets["text_primary"]:
                try:
                    w.config(fg=th["text"])
                except Exception:
                    pass

            for w in themed_widgets["text_dim"]:
                try:
                    w.config(fg=th["text_dim"])
                except Exception:
                    pass

            for w in themed_widgets["text_muted"]:
                try:
                    w.config(fg=th["text_muted"])
                except Exception:
                    pass

            for btn in themed_widgets["pill_buttons"]:
                try:
                    if btn.master == btn_frame:
                        parent_bg = th["surface"]
                    elif btn.master == tab_bar:
                        parent_bg = th["bg"]
                    elif btn.master in themed_widgets["surface"]:
                        parent_bg = th["surface"]
                    else:
                        parent_bg = th["card"]
                    btn.set_theme(
                        bg_parent=parent_bg,
                        fill_primary=th["accent"],
                        text_primary=th["accent_text"],
                        fill_secondary=th["btn_bg"],
                        text_secondary=th["btn_fg"],
                        border_color=th["btn_border"]
                    )
                except Exception:
                    pass

            for c in themed_widgets["consoles"]:
                try:
                    c.config(
                        bg=th["console_bg"],
                        fg=th["console_fg"],
                        insertbackground=th["text"],
                        highlightbackground=th["border"],
                        highlightcolor=th["border"]
                    )
                except Exception:
                    pass

            for dial, container_key in themed_widgets["dials"]:
                try:
                    parent_bg = th[container_key] if container_key in th else th["card"]
                    dial.set_theme(
                        bg=parent_bg,
                        active_color=th["dial_active"],
                        inactive_color=th["dial_inactive"],
                        text_color=th["text"],
                        dim_color=th["text_dim"]
                    )
                except Exception:
                    pass

            for wave in themed_widgets["waves"]:
                try:
                    wave.set_theme(bg=th["card"], wave_color=th["wave_color"])
                except Exception:
                    pass

            for toggle, container_key in themed_widgets["pill_toggles"]:
                try:
                    parent_bg = th[container_key] if container_key in th else th["card"]
                    toggle.set_theme(
                        bg_parent=parent_bg,
                        pill_bg_off=th["pill_bg_off"],
                        pill_border_off=th["pill_border_off"],
                        pill_bg_on=th["pill_bg_on"],
                        knob_on=th["pill_knob_on"],
                        knob_off=th["pill_knob_off"]
                    )
                except Exception:
                    pass

            for strip in themed_widgets.get("capsule_strips", []):
                try:
                    strip.set_theme(
                        bg_parent=th["card"],
                        capsule_bg=th["capsule_bg"],
                        capsule_border=th["capsule_border"],
                        text_color=th["text"],
                        dim_color=th["text_dim"],
                        pill_bg_off=th["pill_bg_off"],
                        pill_border_off=th["pill_border_off"],
                        pill_bg_on=th["pill_bg_on"],
                        knob_on=th["pill_knob_on"],
                        knob_off=th["pill_knob_off"]
                    )
                except Exception:
                    pass

            btn_theme.set_text(th["toggle_text"])

            logo_img = get_theme_logo(self.current_theme)
            if logo_img:
                lbl_logo.config(image=logo_img)
                lbl_logo.image = logo_img

            # TTK Styles for Treeviews and Notebook
            style.configure("TNotebook", background=th["bg"], borderwidth=0)
            style.configure(
                "TNotebook.Tab",
                background=th["tab_bg"],
                foreground=th["tab_fg"],
                padding=[16, 8],
                font=("Segoe UI", 10, "bold"),
                borderwidth=1,
                lightcolor=th["border"],
                darkcolor=th["border"]
            )
            style.map(
                "TNotebook.Tab",
                background=[("selected", th["tab_sel_bg"])],
                foreground=[("selected", th["tab_sel_fg"])]
            )

            style.configure(
                "Treeview",
                background=th["tree_bg"],
                foreground=th["tree_fg"],
                fieldbackground=th["tree_bg"],
                font=("Segoe UI", 10),
                rowheight=28,
                borderwidth=0
            )
            style.configure(
                "Treeview.Heading",
                background=th["tree_head_bg"],
                foreground=th["tree_head_fg"],
                font=("Segoe UI", 9, "bold"),
                relief=tk.FLAT,
                padding=[6, 6]
            )
            style.map(
                "Treeview",
                background=[("selected", th["tree_sel_bg"])],
                foreground=[("selected", th["tree_sel_fg"])]
            )

            for tree in themed_widgets["treeviews"]:
                tree.tag_configure("even", background=th["tree_bg"])
                tree.tag_configure("odd", background=th["tree_alt"])

        # -------------------------------------------------------------
        # Telemetry Data Populate
        # -------------------------------------------------------------
        def update_ui_with_report(report):
            self._is_scanning = False
            self.current_report = report
            score = report.health_score

            status_text = "OPTIMAL" if score >= 85 else ("ATTENTION" if score >= 70 else "CRITICAL")
            dial_health.update_value(str(score), float(score), status_text)

            lbl_subtitle.config(text=f"Host: {report.system.hostname} • OS: {report.system.os_name} ({report.system.os_arch}) • Uptime: {report.system.uptime_formatted}")
            btn_scan.set_state(tk.NORMAL)
            btn_scan.set_text("⟳ RE-SCAN")
            btn_overview_scan.set_state(tk.NORMAL)
            btn_overview_scan.set_text("⟳ RE-SCAN")

            # KPI values
            kpi_cpu_v.config(text=report.cpu.model[:24])
            kpi_cpu_s.config(text=f"{report.cpu.physical_cores} Cores / {report.cpu.logical_cores} Threads @ {format_hz(report.cpu.max_clock_mhz)}")
            kpi_mem_v.config(text=format_bytes(report.memory.total_bytes))
            kpi_mem_s.config(text=f"{report.memory.percent}% used ({format_bytes(report.memory.used_bytes)})")

            gpu_name = report.gpu.devices[0].name[:22] if report.gpu.devices else "Integrated GPU"
            kpi_gpu_v.config(text=gpu_name)
            kpi_gpu_s.config(text=report.gpu.devices[0].vram_formatted if report.gpu.devices else "Shared VRAM")

            sec_str = "Secure Boot OK" if report.security.secure_boot else "Secure Boot OFF"
            kpi_sec_v.config(text=sec_str)
            kpi_sec_s.config(text=f"TPM: {'Active' if report.security.tpm_present else 'None'}")

            def populate_tree(tree, rows):
                tree.delete(*tree.get_children())
                for idx, r in enumerate(rows):
                    tag = "even" if idx % 2 == 0 else "odd"
                    tree.insert("", tk.END, values=r, tags=(tag,))

            # Findings
            warn_rows = []
            if report.warnings:
                for w in report.warnings:
                    warn_rows.append((w.level, w.category, f"{w.title}: {w.description}"))
            else:
                warn_rows.append(("HEALTHY", "System", "All hardware components operating with optimal parameters."))
            populate_tree(tree_warn, warn_rows)

            # CPU & Motherboard
            cpu_rows = [
                ("Operating System", f"{report.system.os_name} (Build {report.system.os_build})"),
                ("Kernel & Architecture", f"{report.system.kernel} ({report.system.os_arch})"),
                ("Firmware Boot Mode", report.system.boot_mode),
                ("Processor (CPU)", report.cpu.model),
                ("Cores & Threads", f"{report.cpu.physical_cores} Physical Cores / {report.cpu.logical_cores} Threads"),
                ("Frequencies", f"Max: {format_hz(report.cpu.max_clock_mhz)} (Base: {format_hz(report.cpu.base_clock_mhz)})"),
                ("Cache Architecture", f"L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}"),
                ("Instruction Sets", ", ".join(report.cpu.features[:8])),
                ("Motherboard Vendor", report.motherboard.manufacturer),
                ("Motherboard Model", report.motherboard.product_name),
                ("Motherboard Serial", report.motherboard.serial_number or "N/A"),
                ("BIOS Firmware", f"{report.motherboard.bios_vendor} - v{report.motherboard.bios_version} ({report.motherboard.bios_release_date})"),
                ("Chassis Form Factor", report.motherboard.chassis_type),
                ("System Uptime", report.system.uptime_formatted),
            ]
            populate_tree(tree_cpu, cpu_rows)

            # RAM
            mem_rows = []
            if report.memory.modules:
                for m in report.memory.modules:
                    mem_rows.append((m.bank_label, m.capacity_formatted, m.memory_type, f"{m.speed_mhz} MHz", m.manufacturer, m.part_number))
            else:
                mem_rows.append(("System RAM", format_bytes(report.memory.total_bytes), "RAM", "Standard", "OEM", "N/A"))
            populate_tree(tree_mem, mem_rows)

            # GPU
            gpu_rows = []
            for g in report.gpu.devices:
                gpu_rows.append((g.name, g.vendor, g.vram_formatted, g.driver_version, g.resolution or "N/A"))
            populate_tree(tree_gpu, gpu_rows)

            # Storage
            storage_rows = []
            for d in report.storage.physical_disks:
                storage_rows.append((f"[Physical] {d.model}", d.media_type, d.size_formatted, d.interface_type, d.smart_status, "Physical Disk"))
            for p in report.storage.partitions:
                storage_rows.append((p.mountpoint, p.fstype, p.total_formatted, p.used_formatted, p.free_formatted, f"{p.percent}%"))
            populate_tree(tree_storage, storage_rows)

            # Security & Network
            sec_rows = [
                ("UEFI Secure Boot", "Enabled" if report.security.secure_boot else "Disabled", "Protects boot integrity against unauthorized bootloaders and rootkits"),
                ("TPM 2.0 Security", "Active" if report.security.tpm_present else "Not Detected", f"Spec: {report.security.tpm_version or '2.0'} - Hardware cryptography & BitLocker anchor"),
                ("Hardware Virtualization", "Enabled" if report.security.virtualization_enabled else "Disabled", "Firmware virtualization enabled for WSL2, Hyper-V, Docker, and VMs")
            ]
            for iface in report.network.interfaces:
                if iface.is_up or iface.ipv4:
                    status = "CONNECTED" if iface.is_up else "DISCONNECTED"
                    ips = ", ".join(iface.ipv4) if iface.ipv4 else "No IPv4"
                    sec_rows.append((f"Net: {iface.name}", status, f"MAC: {iface.mac_address} | IP: {ips} | Speed: {iface.speed_mbps} Mbps"))
            populate_tree(tree_sec, sec_rows)

        def run_background_scan():
            rep = self.engine.run_full_scan()
            root.after(0, update_ui_with_report, rep)

        def on_window_close():
            try:
                self.stress_engine.stop_test()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass
            os._exit(0)

        root.protocol("WM_DELETE_WINDOW", on_window_close)

        # Apply initial dark theme
        apply_current_theme()
        root.mainloop()


def launch_gui(prefer_engine: str = "auto") -> None:
    """Convenience launcher for HardwareGauntletGUI."""
    gui = HardwareGauntletGUI()
    gui.run(prefer_engine=prefer_engine)


if __name__ == "__main__":
    launch_gui()
