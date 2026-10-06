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
import platform
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
from hwscan.core.instance_guard import (
    acquire_single_instance_lock,
    WINDOW_TITLE
)
from hwscan.core.cleanup import (
    clean_storage,
    clean_ram,
    clean_cpu,
    clean_network_cache,
    run_full_system_cleanup
)
from hwscan.core.deep_cleanup import (
    clean_component_store,
    clean_driver_and_kernel_store,
    optimize_system_storage_overhead,
    clean_developer_caches,
    run_deep_system_optimization
)
from hwscan.core.hardware_health import (
    audit_thermal_health,
    audit_battery_longevity,
    optimize_ssd_trim,
    run_hardware_health_suite
)
from hwscan.core.physical_maintenance import (
    generate_physical_maintenance_guide,
    get_fan_and_heatsink_cleaning_protocol,
    get_thermal_repasting_advisor,
    get_peripherals_and_ports_hygiene_guide,
    run_physical_maintenance_suite
)
from hwscan.core.startup_service_tuner import (
    audit_startup_applications,
    audit_background_services,
    audit_power_and_latency_profiles,
    run_startup_optimization_suite
)
from hwscan import __version__
from hwscan.core.update_channel import (
    CHANNELS,
    DEFAULT_CHANNEL,
    get_current_channel,
    set_current_channel,
    check_for_updates,
    apply_patch_bundle,
    rollback_patch,
    get_active_patch_metadata,
    download_and_apply_patch
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


POWERSHELL_CLEANUP_COMMANDS: Dict[str, str] = {
    "temp": (
        "& { Get-ChildItem -Path $env:TEMP, 'C:\\Windows\\Temp' -Recurse -Force -ErrorAction SilentlyContinue | "
        "Where-Object { -not $_.PSIsContainer } | Remove-Item -Force -ErrorAction SilentlyContinue; "
        "Write-Output 'User and system temporary files purged.' }"
    ),
    "recycle_bin": (
        "& { Clear-RecycleBin -Force -ErrorAction SilentlyContinue; "
        "Write-Output 'Recycle Bin emptied across all mounted storage volumes.' }"
    ),
    "dns_flush": (
        "& { Clear-DnsClientCache -ErrorAction SilentlyContinue; ipconfig /flushdns; "
        "Write-Output 'DNS client resolver cache and active sockets flushed.' }"
    ),
    "update_cache": (
        "& { Stop-Service -Name wuauserv -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; "
        "Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\Download\\*' -Recurse -Force -ErrorAction SilentlyContinue; "
        "Start-Service -Name wuauserv -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; "
        "Write-Output 'Windows Update software distribution download cache purged.' }"
    ),
    "full_cleanup": (
        "& { Write-Output '=== Commencing Full System Optimization Pipeline ==='; "
        "Get-ChildItem -Path $env:TEMP, 'C:\\Windows\\Temp' -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Remove-Item -Force -ErrorAction SilentlyContinue; "
        "Write-Output '[1/4] Temp files purged.'; "
        "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; "
        "Write-Output '[2/4] Recycle Bin emptied.'; "
        "Clear-DnsClientCache -ErrorAction SilentlyContinue; ipconfig /flushdns; "
        "Write-Output '[3/4] DNS cache flushed.'; "
        "Stop-Service -Name wuauserv -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; "
        "Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\Download\\*' -Recurse -Force -ErrorAction SilentlyContinue; "
        "Start-Service -Name wuauserv -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; "
        "Write-Output '[4/4] Windows Update download cache purged.'; "
        "Write-Output '=== Full System Optimization Finished ===' }"
    )
}


def execute_powershell_cleanup(script: str, timeout: int = 60) -> Tuple[int, str, str]:
    """Execute a powershell cleanup command silently without console flashing and return (returncode, stdout, stderr)."""
    if sys.platform != "win32":
        return 0, "PowerShell cleanup requires Windows environment.", ""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out or "", err or ""
    except Exception as ex:
        return 1, "", str(ex)


def get_asset_file_path(filename: str) -> str:
    """Resolve asset paths for standalone portable executable, PyInstaller bundle, or local source."""
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


class BentoSparklineCanvas(tk.Canvas):
    """Dynamic multi-segment bar sparkline for Bento-Box Studio hero cards."""

    def __init__(self, parent, width=320, height=54, bar_count=18, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bd=0, **kwargs)
        self.w = width
        self.h = height
        self.bar_count = bar_count
        self.values = [0.35, 0.42, 0.38, 0.55, 0.48, 0.62, 0.58, 0.72, 0.65, 0.80, 0.75, 0.68, 0.74, 0.82, 0.78, 0.85, 0.82, 0.88]
        self.bg_color = "#15151a"
        self.bar_color = "#3b82f6"
        self.bar_highlight = "#60a5fa"
        self.bind("<Configure>", self._on_resize)
        self.draw()

    def _on_resize(self, event):
        if event.width > 20 and event.height > 10:
            self.w = event.width
            self.h = event.height
            self.draw()

    def set_theme(self, bg: str, bar_color: str, bar_highlight: str):
        self.bg_color = bg
        self.bar_color = bar_color
        self.bar_highlight = bar_highlight
        self.configure(bg=bg)
        self.draw()

    def update_history(self, new_val: float):
        """Append normalized 0.0-1.0 value and redraw sparkline."""
        clamped = max(0.1, min(1.0, float(new_val)))
        self.values.append(clamped)
        if len(self.values) > self.bar_count:
            self.values.pop(0)
        self.draw()

    def draw(self):
        self.delete("all")
        n = len(self.values)
        if n == 0:
            return

        spacing = 4
        total_spacing = spacing * (n - 1)
        avail_w = max(10, self.w - 12 - total_spacing)
        bar_w = max(3.0, avail_w / float(n))

        x_start = 6.0
        for i, val in enumerate(self.values):
            x1 = x_start + i * (bar_w + spacing)
            x2 = x1 + bar_w
            bar_h = max(4.0, (self.h - 10) * val)
            y1 = self.h - 5 - bar_h
            y2 = self.h - 5

            color = self.bar_highlight if i >= n - 3 else self.bar_color
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline="", width=0)


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
        root.update_idletasks()

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
            "sparklines": [],
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

        def toggle_theme():
            self.current_theme = "light" if self.current_theme == "dark" else "dark"
            apply_current_theme()

        def launch_os_tool(tool_cmd):
            try:
                subprocess.Popen(tool_cmd, shell=True)
            except Exception as err:
                messagebox.showerror("Tool Error", f"Unable to launch {tool_cmd}:\n{err}")

        def open_update_channel_modal():
            win = tk.Toplevel(root)
            win.title("Hardware Gauntlet — Update Channel Manager")
            win.geometry("590x490")
            win.minsize(520, 440)
            win.transient(root)

            th = THEMES[self.current_theme]
            win.configure(bg=th["root_bg"])

            container = tk.Frame(win, bg=th["root_bg"], padx=24, pady=20)
            container.pack(fill=tk.BOTH, expand=True)

            lbl_mtitle = tk.Label(container, text="UPDATE CHANNEL & MODULAR PATCHING", font=("Segoe UI", 12, "bold"), fg=th["text_primary"], bg=th["root_bg"])
            lbl_mtitle.pack(anchor="w")

            lbl_msub = tk.Label(container, text="Push and receive in-place upgrades without replacing your standalone executable.", font=("Segoe UI", 8), fg=th["text_dim"], bg=th["root_bg"])
            lbl_msub.pack(anchor="w", pady=(2, 14))

            # Channel Card
            card = tk.Frame(container, bg=th["card"], highlightbackground=th["border"], highlightthickness=1, padx=16, pady=12)
            card.pack(fill=tk.X, pady=(0, 12))

            row_sel = tk.Frame(card, bg=th["card"])
            row_sel.pack(fill=tk.X, pady=(0, 8))

            lbl_c_prompt = tk.Label(row_sel, text="Active Channel:", font=("Segoe UI", 9, "bold"), fg=th["text_primary"], bg=th["card"])
            lbl_c_prompt.pack(side=tk.LEFT)

            cur_ch = get_current_channel()
            combo_var = tk.StringVar(value=cur_ch.upper())
            combo_box = ttk.Combobox(row_sel, textvariable=combo_var, values=["STABLE", "BETA", "NIGHTLY"], state="readonly", width=12)
            combo_box.pack(side=tk.LEFT, padx=(10, 0))

            def on_select_ch(e):
                new_c = combo_var.get().lower()
                set_current_channel(new_c)
                append_log(f"Switched active update channel to {new_c.upper()}")

            combo_box.bind("<<ComboboxSelected>>", on_select_ch)

            patch_meta = get_active_patch_metadata()
            patch_disp = f"v{patch_meta.get('version')}" if patch_meta else "None (Factory Binary)"
            lbl_meta_text = tk.Label(card, text=f"Base Executable: v{__version__}  •  Active Hot-Patch: {patch_disp}", font=("Segoe UI", 8), fg=th["text_dim"], bg=th["card"])
            lbl_meta_text.pack(anchor="w")

            # Status log
            lbl_log_h = tk.Label(container, text="CHANNEL LOG & STATUS —", font=("Segoe UI", 8, "bold"), fg=th["text_dim"], bg=th["root_bg"])
            lbl_log_h.pack(anchor="w", pady=(2, 4))

            log_box = tk.Text(container, height=7, bg=th["card_alt"], fg=th["text_primary"], font=("Consolas", 8), relief="flat", highlightbackground=th["border"], highlightthickness=1, padx=8, pady=8)
            log_box.pack(fill=tk.X, pady=(0, 14))
            log_box.insert("end", f"[*] Channel: {cur_ch.upper()} | Base: v{__version__}\n[*] Ready to query remote manifest or load local patch bundles.\n")
            log_box.config(state="disabled")

            def append_log(msg):
                log_box.config(state="normal")
                log_box.insert("end", f"{msg}\n")
                log_box.see("end")
                log_box.config(state="disabled")

            actions_f = tk.Frame(container, bg=th["root_bg"])
            actions_f.pack(fill=tk.X)

            latest_m = [None]

            def on_check():
                ch = combo_var.get().lower()
                append_log(f"[*] Checking channel '{ch.upper()}' for updates...")
                btn_c.set_state(tk.DISABLED)

                def bg_chk():
                    has_u, manifest, msg = check_for_updates(ch)
                    def fin():
                        btn_c.set_state(tk.NORMAL)
                        append_log(f"[{'✓' if has_u else '*'}] {msg}")
                        if manifest and has_u:
                            latest_m[0] = manifest
                            btn_a.set_state(tk.NORMAL)
                            append_log(f"Ready to apply patch: v{manifest.version} ({manifest.patch_size_bytes} bytes)")
                            for n in manifest.notes:
                                append_log(f"  • {n}")
                    win.after(0, fin)

                threading.Thread(target=bg_chk, daemon=True).start()

            def on_apply_remote():
                if not latest_m[0]:
                    messagebox.showinfo("Check Required", "Please check for updates first.")
                    return
                m = latest_m[0]
                append_log(f"[*] Downloading and applying patch v{m.version}...")
                btn_a.set_state(tk.DISABLED)

                def bg_dl():
                    ok, msg = download_and_apply_patch(m, log_fn=append_log)
                    def fin_dl():
                        btn_a.set_state(tk.NORMAL)
                        if ok:
                            messagebox.showinfo("Update Complete", f"Patch v{m.version} applied successfully!\nModules are loaded dynamically into runtime.")
                            win.destroy()
                        else:
                            messagebox.showerror("Update Error", msg)
                    win.after(0, fin_dl)

                threading.Thread(target=bg_dl, daemon=True).start()

            def on_apply_local():
                f = filedialog.askopenfilename(
                    parent=win,
                    title="Select Hot-Patch ZIP Bundle",
                    filetypes=[("Zip Patches", "*.zip"), ("All Files", "*.*")]
                )
                if f:
                    append_log(f"[*] Applying local patch: {os.path.basename(f)}...")
                    ok, msg = apply_patch_bundle(f, expected_sha256="")
                    append_log(f"[{'✓' if ok else '!'}] {msg}")
                    if ok:
                        messagebox.showinfo("Local Patch Applied", f"Local patch bundle applied successfully!\nModules are loaded immediately into runtime path.")
                        win.destroy()
                    else:
                        messagebox.showerror("Patch Error", msg)

            def on_rollback():
                if messagebox.askyesno("Rollback Patch", "Rollback active hot-patch and restore factory standalone executable?"):
                    ok, msg = rollback_patch()
                    append_log(f"[{'✓' if ok else '!'}] {msg}")
                    if ok:
                        messagebox.showinfo("Rollback Complete", "Reverted cleanly to factory standalone binary.")
                        win.destroy()

            btn_c = PillButton(actions_f, text="🔍 CHECK UPDATES", command=on_check, width=130, height=32, is_primary=True)
            btn_c.pack(side=tk.LEFT, padx=(0, 6))

            btn_a = PillButton(actions_f, text="📥 APPLY UPDATE", command=on_apply_remote, width=120, height=32, is_primary=False)
            btn_a.pack(side=tk.LEFT, padx=(0, 6))
            btn_a.set_state(tk.DISABLED)

            btn_l = PillButton(actions_f, text="📂 LOAD LOCAL ZIP", command=on_apply_local, width=130, height=32, is_primary=False)
            btn_l.pack(side=tk.LEFT, padx=(0, 6))

            btn_r = PillButton(actions_f, text="↺ ROLLBACK", command=on_rollback, width=96, height=32, is_primary=False)
            btn_r.pack(side=tk.LEFT)

        # Pill Buttons in Header
        btn_scan = PillButton(btn_frame, text="▶ RUN SCAN", command=do_scan, width=116, height=32, is_primary=True)
        btn_scan.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_scan)

        btn_channel = PillButton(btn_frame, text="⚡ UPDATE", command=open_update_channel_modal, width=88, height=32, is_primary=False)
        btn_channel.pack(side=tk.LEFT, padx=3)
        themed_widgets["pill_buttons"].append(btn_channel)

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

        self._root = root
        self._switch_tab = switch_tab

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
        # Tab 1: Concept 3 — Bento-Box Modular Studio Architecture
        # -------------------------------------------------------------
        bento_container = tk.Frame(tab_overview)
        bento_container.pack(fill=tk.X, pady=(0, 14))
        themed_widgets["root_bg"].append(bento_container)

        # -------------------------------------------------------------
        # BENTO BLOCK 1: Hero 2x2 Thermal & Clock Dynamics Card (Left)
        # -------------------------------------------------------------
        bento_hero = tk.Frame(bento_container, width=440, padx=22, pady=16, highlightthickness=1)
        bento_hero.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 14))
        themed_widgets["cards"].append(bento_hero)
        themed_widgets["borders"].append(bento_hero)

        hero_top_bar = tk.Frame(bento_hero)
        hero_top_bar.pack(fill=tk.X)
        themed_widgets["cards"].append(hero_top_bar)

        lbl_hero_tag = tk.Label(hero_top_bar, text="THERMAL & CLOCK DYNAMICS", font=("Segoe UI", 9, "bold"))
        lbl_hero_tag.pack(side=tk.LEFT)
        themed_widgets["cards"].append(lbl_hero_tag)
        themed_widgets["text_primary"].append(lbl_hero_tag)

        lbl_hero_badge = tk.Label(hero_top_bar, text="STABLE", font=("Segoe UI", 8, "bold"), fg="#10b981", bg="#15151a")
        lbl_hero_badge.pack(side=tk.RIGHT)
        themed_widgets["cards"].append(lbl_hero_badge)

        # Hero Middle Row: Dial + Numeric Readout
        hero_mid_row = tk.Frame(bento_hero)
        hero_mid_row.pack(fill=tk.X, pady=(4, 6))
        themed_widgets["cards"].append(hero_mid_row)

        dial_health = RadialDialWidget(hero_mid_row, size=116, title="INTEGRITY", value_str="--", sub_str="READY", percent=0.0)
        dial_health.pack(side=tk.LEFT, padx=(0, 14))
        themed_widgets["dials"].append((dial_health, "cards"))

        hero_text_col = tk.Frame(hero_mid_row)
        hero_text_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        themed_widgets["cards"].append(hero_text_col)

        hero_val_row = tk.Frame(hero_text_col)
        hero_val_row.pack(anchor="w", pady=(0, 2))
        themed_widgets["cards"].append(hero_val_row)

        lbl_hero_temp = tk.Label(hero_val_row, text="58", font=("Segoe UI", 30, "bold"))
        lbl_hero_temp.pack(side=tk.LEFT)
        themed_widgets["cards"].append(lbl_hero_temp)
        themed_widgets["text_primary"].append(lbl_hero_temp)

        lbl_hero_unit = tk.Label(hero_val_row, text="°C", font=("Segoe UI", 16, "bold"), fg="#3b82f6")
        lbl_hero_unit.pack(side=tk.LEFT, padx=(2, 0), pady=(8, 0))
        themed_widgets["cards"].append(lbl_hero_unit)

        lbl_hero_clock = tk.Label(hero_text_col, text="CPU Package Temp • 4.80 GHz Boost", font=("Segoe UI", 8))
        lbl_hero_clock.pack(anchor="w", pady=(0, 4))
        themed_widgets["cards"].append(lbl_hero_clock)
        themed_widgets["text_dim"].append(lbl_hero_clock)

        # Interactive Multi-Bar Sparkline History
        bento_sparkline = BentoSparklineCanvas(bento_hero, width=380, height=52)
        bento_sparkline.pack(fill=tk.X, pady=(4, 10))
        themed_widgets["sparklines"].append((bento_sparkline, "cards"))

        # Action row inside Hero Block
        hero_btn_row = tk.Frame(bento_hero)
        hero_btn_row.pack(fill=tk.X, pady=(6, 8))
        themed_widgets["cards"].append(hero_btn_row)

        btn_overview_scan = PillButton(hero_btn_row, text="▶ RUN AUDIT", command=do_scan, width=120, height=30, is_primary=True)
        btn_overview_scan.pack(side=tk.LEFT, padx=(0, 6))
        themed_widgets["pill_buttons"].append(btn_overview_scan)

        btn_overview_export = PillButton(hero_btn_row, text="📄 REPORT", command=do_export_html, width=105, height=30, is_primary=False)
        btn_overview_export.pack(side=tk.LEFT)
        themed_widgets["pill_buttons"].append(btn_overview_export)

        # Footer Metrics Row inside Hero Block
        hero_footer = tk.Frame(bento_hero)
        hero_footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(6, 0))
        themed_widgets["cards"].append(hero_footer)

        lbl_hero_tjmax = tk.Label(hero_footer, text="TjMax Delta: 42°C Headroom", font=("Segoe UI", 8, "bold"))
        lbl_hero_tjmax.pack(side=tk.LEFT)
        themed_widgets["cards"].append(lbl_hero_tjmax)
        themed_widgets["text_dim"].append(lbl_hero_tjmax)

        lbl_hero_fan = tk.Label(hero_footer, text="Fan: 1,350 RPM", font=("Segoe UI", 8))
        lbl_hero_fan.pack(side=tk.RIGHT)
        themed_widgets["cards"].append(lbl_hero_fan)
        themed_widgets["text_dim"].append(lbl_hero_fan)

        # -------------------------------------------------------------
        # BENTO RIGHT COLUMN: 1x1 Tiles & Wide Action Banner
        # -------------------------------------------------------------
        bento_right = tk.Frame(bento_container)
        bento_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        themed_widgets["root_bg"].append(bento_right)

        # Top Row of Right Column: 1x1 Memory Tile & 1x1 SSD Health Tile
        bento_top_tiles = tk.Frame(bento_right)
        bento_top_tiles.pack(fill=tk.X, pady=(0, 10))
        themed_widgets["root_bg"].append(bento_top_tiles)

        # Tile 1: Memory Allocation
        tile_mem = tk.Frame(bento_top_tiles, padx=16, pady=12, highlightthickness=1)
        tile_mem.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        themed_widgets["cards"].append(tile_mem)
        themed_widgets["borders"].append(tile_mem)

        lbl_tmem_hdr = tk.Label(tile_mem, text="MEMORY ALLOCATION", font=("Segoe UI", 8, "bold"))
        lbl_tmem_hdr.pack(anchor="w")
        themed_widgets["cards"].append(lbl_tmem_hdr)
        themed_widgets["text_dim"].append(lbl_tmem_hdr)

        lbl_tmem_val = tk.Label(tile_mem, text="8.2 / 32 GB", font=("Segoe UI", 13, "bold"))
        lbl_tmem_val.pack(anchor="w", pady=(4, 2))
        themed_widgets["cards"].append(lbl_tmem_val)
        themed_widgets["text_primary"].append(lbl_tmem_val)

        # Horizontal capacity bar
        mem_bar_bg = tk.Frame(tile_mem, height=6, bg="#2a2a34")
        mem_bar_bg.pack(fill=tk.X, pady=(3, 8))
        mem_bar_fill = tk.Frame(mem_bar_bg, height=6, width=65, bg="#6366f1")
        mem_bar_fill.place(x=0, y=0, relheight=1.0, relwidth=0.26)

        btn_tmem_trim = PillButton(tile_mem, text="TRIM RAM", command=clean_ram, width=110, height=26, is_primary=False)
        btn_tmem_trim.pack(anchor="w")
        themed_widgets["pill_buttons"].append(btn_tmem_trim)

        # Tile 2: SSD Health & TRIM
        tile_ssd = tk.Frame(bento_top_tiles, padx=16, pady=12, highlightthickness=1)
        tile_ssd.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))
        themed_widgets["cards"].append(tile_ssd)
        themed_widgets["borders"].append(tile_ssd)

        lbl_tssd_hdr = tk.Label(tile_ssd, text="SSD HEALTH & WEAR", font=("Segoe UI", 8, "bold"))
        lbl_tssd_hdr.pack(anchor="w")
        themed_widgets["cards"].append(lbl_tssd_hdr)
        themed_widgets["text_dim"].append(lbl_tssd_hdr)

        lbl_tssd_val = tk.Label(tile_ssd, text="99% (32% FREE)", font=("Segoe UI", 13, "bold"), fg="#10b981")
        lbl_tssd_val.pack(anchor="w", pady=(4, 2))
        themed_widgets["cards"].append(lbl_tssd_val)

        lbl_tssd_sub = tk.Label(tile_ssd, text="SLC Over-Provisioning Headroom", font=("Segoe UI", 8))
        lbl_tssd_sub.pack(anchor="w", pady=(0, 6))
        themed_widgets["cards"].append(lbl_tssd_sub)
        themed_widgets["text_dim"].append(lbl_tssd_sub)

        btn_tssd_trim = PillButton(tile_ssd, text="ISSUE RETRIM", command=optimize_ssd_trim, width=120, height=26, is_primary=False)
        btn_tssd_trim.pack(anchor="w")
        themed_widgets["pill_buttons"].append(btn_tssd_trim)

        # Bottom Tile of Right Column: 2x1 Wide Action Banner
        tile_purge_banner = tk.Frame(bento_right, padx=18, pady=12, highlightthickness=1)
        tile_purge_banner.pack(fill=tk.BOTH, expand=True)
        themed_widgets["cards"].append(tile_purge_banner)
        themed_widgets["borders"].append(tile_purge_banner)

        purge_info_box = tk.Frame(tile_purge_banner)
        purge_info_box.pack(side=tk.LEFT, fill=tk.Y)
        themed_widgets["cards"].append(purge_info_box)

        lbl_purge_title = tk.Label(purge_info_box, text="OS DEEP STORAGE HYGIENE & TOOLCHAINS", font=("Segoe UI", 10, "bold"))
        lbl_purge_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_purge_title)
        themed_widgets["text_primary"].append(lbl_purge_title)

        lbl_purge_sub = tk.Label(purge_info_box, text="WinSxS component store, stale driver packages, and dev caches ready for purge", font=("Segoe UI", 8))
        lbl_purge_sub.pack(anchor="w", pady=(2, 0))
        themed_widgets["cards"].append(lbl_purge_sub)
        themed_widgets["text_dim"].append(lbl_purge_sub)

        btn_purge_action = PillButton(
            tile_purge_banner,
            text="PURGE 2.4 GB",
            command=run_deep_system_optimization,
            width=140,
            height=32,
            is_primary=True
        )
        btn_purge_action.pack(side=tk.RIGHT)
        themed_widgets["pill_buttons"].append(btn_purge_action)

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

        lbl_win_bench = tk.Label(win_tools_box, text=f"{platform.system().upper()} BENCHMARKS —", font=("Segoe UI", 9, "bold"))
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
        elif sys.platform == "darwin":
            add_quick_tool("🧠 MEMORY MONITOR", "open -a 'Activity Monitor'")
            add_quick_tool("📈 SYSTEM PROFILER", "system_profiler SPHardwareDataType")
            add_quick_tool("⚡ STORAGE CHECK", "diskutil list")
            add_quick_tool("🎮 DISPLAY REPORT", "system_profiler SPDisplaysDataType")
        else:
            add_quick_tool("🧠 MEMORY CHECK", "free -h")
            add_quick_tool("📈 SYSTEM TOP", "x-terminal-emulator -e top || gnome-system-monitor")
            add_quick_tool("⚡ STORAGE IO", "x-terminal-emulator -e iostat -x 1 5 || df -h")
            add_quick_tool("🎮 PCI BUS REPORT", "x-terminal-emulator -e lspci")

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
        # Tab 8: System Tools, Diagnostics & Installation (Scrollable)
        # -------------------------------------------------------------
        canvas_tools = tk.Canvas(tab_tools, highlightthickness=0, bd=0)
        scroll_tools = ttk.Scrollbar(tab_tools, orient=tk.VERTICAL, command=canvas_tools.yview)
        tools_scroll_content = tk.Frame(canvas_tools)

        tools_scroll_content.bind(
            "<Configure>",
            lambda e: canvas_tools.configure(scrollregion=canvas_tools.bbox("all"))
        )
        canvas_window = canvas_tools.create_window((0, 0), window=tools_scroll_content, anchor="nw")

        def _on_canvas_configure(event):
            canvas_tools.itemconfig(canvas_window, width=event.width)

        canvas_tools.bind("<Configure>", _on_canvas_configure)
        canvas_tools.configure(yscrollcommand=scroll_tools.set)

        # Mouse wheel support
        def _on_mousewheel(event):
            canvas_tools.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas_tools.bind_all("<MouseWheel>", lambda e: _on_mousewheel(e) if active_tab_idx[0] == 7 else None)

        canvas_tools.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tools.pack(side=tk.RIGHT, fill=tk.Y)
        themed_widgets["root_bg"].append(canvas_tools)
        themed_widgets["root_bg"].append(tools_scroll_content)

        lbl_tools_hdr = tk.Label(tools_scroll_content, text="DIRECT OPERATING SYSTEM DIAGNOSTIC SHORTCUTS —", font=("Segoe UI", 11, "bold"))
        lbl_tools_hdr.pack(anchor="w", pady=(0, 14))
        themed_widgets["root_bg"].append(lbl_tools_hdr)
        themed_widgets["text_primary"].append(lbl_tools_hdr)

        tools_grid = tk.Frame(tools_scroll_content)
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
        elif sys.platform == "darwin":
            add_tool_card(tools_grid, "📈 Activity Monitor", "Real-time thread utilization", "open -a 'Activity Monitor'")
            add_tool_card(tools_grid, "💾 Disk Utility", "Partition layouts & health", "open -a 'Disk Utility'")
            add_tool_card(tools_grid, "ℹ️ System Info", "Hardware & firmware specs", "open -a 'System Information'")
            add_tool_card(tools_grid, "📜 System Console", "Kernel logs & diagnostic reports", "open -a 'Console'")
        else:
            add_tool_card(tools_grid, "📈 System Monitor", "Real-time thread utilization", "gnome-system-monitor")
            add_tool_card(tools_grid, "💾 Disk Utility", "Partition layouts & health", "gnome-disks")
            add_tool_card(tools_grid, "ℹ️ Hardware Lister", "Kernel hardware topology", "hardinfo")
            add_tool_card(tools_grid, "🔌 Device Control", "Drivers & PCI/USB buses", "x-terminal-emulator -e lspci")

        # -------------------------------------------------------------
        # CARD 05 — All-Round System Optimization (Storage, RAM, CPU & Network)
        # -------------------------------------------------------------
        cleanup_card = tk.Frame(tools_scroll_content, padx=18, pady=14, highlightthickness=1)
        cleanup_card.pack(fill=tk.X, pady=(0, 14))
        themed_widgets["surface"].append(cleanup_card)
        themed_widgets["borders"].append(cleanup_card)

        clean_hdr_row = tk.Frame(cleanup_card)
        clean_hdr_row.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(clean_hdr_row)

        lbl_clean_title = tk.Label(clean_hdr_row, text="CARD 05 — ALL-ROUND SYSTEM OPTIMIZATION (STORAGE, RAM & CPU)", font=("Segoe UI", 11, "bold"))
        lbl_clean_title.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_clean_title)
        themed_widgets["text_primary"].append(lbl_clean_title)

        lbl_clean_sub = tk.Label(
            cleanup_card,
            text=f"Automated hardware-aligned maintenance engine for Storage, RAM, CPU & Network (Active Platform: {platform.system()}).",
            font=("Segoe UI", 8)
        )
        lbl_clean_sub.pack(anchor="w", pady=(0, 8))
        themed_widgets["surface"].append(lbl_clean_sub)
        themed_widgets["text_dim"].append(lbl_clean_sub)

        # Execution console inside cleanup card
        clean_console_frame = tk.Frame(cleanup_card, highlightthickness=1)
        clean_console_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))
        themed_widgets["surface"].append(clean_console_frame)
        themed_widgets["borders"].append(clean_console_frame)

        clean_console_bar = tk.Frame(clean_console_frame, padx=8, pady=3)
        clean_console_bar.pack(fill=tk.X)
        themed_widgets["surface"].append(clean_console_bar)

        lbl_clean_console = tk.Label(clean_console_bar, text="SYSTEM OPTIMIZATION STREAM [CROSS-PLATFORM] —", font=("Segoe UI", 8, "bold"))
        lbl_clean_console.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_clean_console)
        themed_widgets["text_dim"].append(lbl_clean_console)

        txt_clean_log = tk.Text(clean_console_frame, font=("Consolas", 8), relief=tk.FLAT, padx=8, pady=4, height=4)
        txt_clean_log.pack(fill=tk.X)
        themed_widgets["consoles"].append(txt_clean_log)

        def log_clean(msg: str):
            timestamp = time.strftime("%H:%M:%S")
            txt_clean_log.insert(tk.END, f"[{timestamp}] {msg}\n")
            txt_clean_log.see(tk.END)

        log_clean(f"All-Round System Optimizer online for {platform.system()} ({platform.machine()}).")
        log_clean("Select a subsystem optimization module below or trigger full pipeline.")

        def run_cleanup_worker(action_name: str, target_fn: Callable):
            def worker():
                root.after(0, lambda: log_clean(f"Executing: {action_name}..."))
                try:
                    target_fn(log_fn=lambda m: root.after(0, lambda msg=m: log_clean(msg)))
                except Exception as ex:
                    root.after(0, lambda: log_clean(f"Execution error: {ex}"))

            threading.Thread(target=worker, daemon=True).start()

        btn_deep_clean = PillButton(
            clean_hdr_row,
            text="🚀 DEEP OS CLEANUP",
            command=lambda: run_cleanup_worker("Deep Software & OS Component Suite", run_deep_system_optimization),
            width=175,
            height=30,
            is_primary=False
        )
        btn_deep_clean.pack(side=tk.RIGHT, padx=(4, 0))
        themed_widgets["pill_buttons"].append(btn_deep_clean)

        btn_full_clean = PillButton(
            clean_hdr_row,
            text="⚡ STANDARD OPTIMIZE",
            command=lambda: run_cleanup_worker("Full Standard Optimization Pipeline", run_full_system_cleanup),
            width=175,
            height=30,
            is_primary=True
        )
        btn_full_clean.pack(side=tk.RIGHT)
        themed_widgets["pill_buttons"].append(btn_full_clean)

        clean_grid = tk.Frame(cleanup_card)
        clean_grid.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(clean_grid)

        def add_clean_tile(parent, title, desc, action_text, fn, target_name):
            tile = tk.Frame(parent, padx=12, pady=8, highlightthickness=1)
            tile.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            themed_widgets["cards"].append(tile)
            themed_widgets["borders"].append(tile)

            t = tk.Label(tile, text=title, font=("Segoe UI", 9, "bold"))
            t.pack(anchor="w")
            themed_widgets["cards"].append(t)
            themed_widgets["text_primary"].append(t)

            d = tk.Label(tile, text=desc, font=("Segoe UI", 8))
            d.pack(anchor="w", pady=(2, 6))
            themed_widgets["cards"].append(d)
            themed_widgets["text_dim"].append(d)

            b = PillButton(tile, text=action_text, command=lambda: run_cleanup_worker(target_name, fn), width=150, height=28, is_primary=False)
            b.pack(fill=tk.X)
            themed_widgets["pill_buttons"].append(b)

        add_clean_tile(clean_grid, "💾 Storage Purge", "Temp, Trash & Caches", "PURGE STORAGE", clean_storage, "Storage Purge")
        add_clean_tile(clean_grid, "⚡ RAM Reclamation", "Trim Working Sets & Standby", "RECLAIM RAM", clean_ram, "RAM Working Set Reclamation")
        add_clean_tile(clean_grid, "🧠 CPU & Processes", "Reap Zombies & Tune Queues", "OPTIMIZE CPU", clean_cpu, "CPU & Process Optimization")
        add_clean_tile(clean_grid, "🌐 Network & DNS", "Flush Resolver & Sockets", "FLUSH DNS", clean_network_cache, "Network & DNS Resolver Flush")

        lbl_deep_sub = tk.Label(cleanup_card, text="DEEP OS COMPONENT & DEVELOPER TOOLCHAINS —", font=("Segoe UI", 8, "bold"))
        lbl_deep_sub.pack(anchor="w", pady=(6, 2))
        themed_widgets["surface"].append(lbl_deep_sub)
        themed_widgets["text_dim"].append(lbl_deep_sub)

        deep_clean_grid = tk.Frame(cleanup_card)
        deep_clean_grid.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(deep_clean_grid)

        add_clean_tile(deep_clean_grid, "🛠️ Component Store", "WinSxS & Package Cache", "CLEAN STORE", clean_component_store, "Component Store Optimization")
        add_clean_tile(deep_clean_grid, "🚗 Driver Store", "Audit OEM INF Packages", "AUDIT DRIVERS", clean_driver_and_kernel_store, "Driver & Kernel Store Audit")
        add_clean_tile(deep_clean_grid, "🔋 System Overhead", "Hiberfil & Log Vacuum", "TRIM OVERHEAD", optimize_system_storage_overhead, "System Overhead Optimization")
        add_clean_tile(deep_clean_grid, "📦 Developer Caches", "Docker, NPM, Pip, Cargo", "PURGE DEV CACHES", clean_developer_caches, "Developer Cache Purge")

        lbl_hw_sub = tk.Label(cleanup_card, text="HARDWARE HEALTH, THERMAL HEADROOM & SSD HYGIENE —", font=("Segoe UI", 8, "bold"))
        lbl_hw_sub.pack(anchor="w", pady=(6, 2))
        themed_widgets["surface"].append(lbl_hw_sub)
        themed_widgets["text_dim"].append(lbl_hw_sub)

        hw_clean_grid = tk.Frame(cleanup_card)
        hw_clean_grid.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(hw_clean_grid)

        add_clean_tile(hw_clean_grid, "🌡️ Thermals & Paste", "Audit TjMax & Dust Delta", "AUDIT THERMALS", audit_thermal_health, "Thermal & Heatsink Audit")
        add_clean_tile(hw_clean_grid, "🔋 Battery Longevity", "Wear Level & 80% Threshold", "AUDIT BATTERY", audit_battery_longevity, "Battery Longevity Audit")
        add_clean_tile(hw_clean_grid, "💽 SSD ReTRIM & Health", "Hardware TRIM & SLC Margins", "OPTIMIZE SSD", optimize_ssd_trim, "SSD TRIM Optimization")
        add_clean_tile(hw_clean_grid, "🛡️ Full Hardware Audit", "Thermals, Battery & Storage", "RUN HW AUDIT", run_hardware_health_suite, "Full Hardware Health Suite")

        lbl_phys_sub = tk.Label(cleanup_card, text="PHYSICAL MAINTENANCE & HARDWARE LIFESPAN PROTOCOLS —", font=("Segoe UI", 8, "bold"))
        lbl_phys_sub.pack(anchor="w", pady=(6, 2))
        themed_widgets["surface"].append(lbl_phys_sub)
        themed_widgets["text_dim"].append(lbl_phys_sub)

        phys_clean_grid = tk.Frame(cleanup_card)
        phys_clean_grid.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(phys_clean_grid)

        add_clean_tile(phys_clean_grid, "📋 System Plan", "Chassis-Tailored Checklist", "GENERATE PLAN", generate_physical_maintenance_guide, "Physical Maintenance Plan")
        add_clean_tile(phys_clean_grid, "💨 Fan & Dust De-Clog", "Back-EMF Bearing Safety", "DUST PROTOCOL", lambda log_fn=None: run_physical_maintenance_suite(log_fn), "Fan & Dust Safety Protocol")
        add_clean_tile(phys_clean_grid, "🧪 Thermal Repasting", "PTM7950 & TIM Advisor", "REPASTE GUIDE", lambda log_fn=None: run_physical_maintenance_suite(log_fn), "Thermal Repasting Advisor")
        add_clean_tile(phys_clean_grid, "🖥️ Screen & Port Care", "USB-C Lint & AR Coatings", "PORT/SCREEN CARE", lambda log_fn=None: run_physical_maintenance_suite(log_fn), "Peripherals & Port Hygiene")

        lbl_tune_sub = tk.Label(cleanup_card, text="STARTUP HYGIENE, BACKGROUND SERVICES & LATENCY TUNER —", font=("Segoe UI", 8, "bold"))
        lbl_tune_sub.pack(anchor="w", pady=(6, 2))
        themed_widgets["surface"].append(lbl_tune_sub)
        themed_widgets["text_dim"].append(lbl_tune_sub)

        tune_clean_grid = tk.Frame(cleanup_card)
        tune_clean_grid.pack(fill=tk.X, pady=(0, 4))
        themed_widgets["surface"].append(tune_clean_grid)

        add_clean_tile(tune_clean_grid, "🚀 Startup Audit", "Impact Scores & Delay", "AUDIT STARTUP", audit_startup_applications, "Startup Application Audit")
        add_clean_tile(tune_clean_grid, "⚙️ Service Profiler", "Telemetry & Pollers", "PROFILE SERVICES", audit_background_services, "Service Overhead Profiler")
        add_clean_tile(tune_clean_grid, "⚡ Power & Latency", "Core Parking & Plans", "AUDIT POWER", audit_power_and_latency_profiles, "Power & Latency Profiler")
        add_clean_tile(tune_clean_grid, "🛡️ Full Startup Suite", "Unified Latency Analysis", "RUN STARTUP SUITE", run_startup_optimization_suite, "Startup & Latency Suite")

        # Installation & System Registration Card
        install_card = tk.Frame(tools_scroll_content, padx=20, pady=16, highlightthickness=1)
        install_card.pack(fill=tk.BOTH, expand=True)
        themed_widgets["surface"].append(install_card)
        themed_widgets["borders"].append(install_card)

        lbl_inst_title = tk.Label(install_card, text="CARD 06 — SINGLE-INSTANCE APPLICATION ARCHITECTURE", font=("Segoe UI", 11, "bold"))
        lbl_inst_title.pack(anchor="w")
        themed_widgets["surface"].append(lbl_inst_title)
        themed_widgets["text_primary"].append(lbl_inst_title)

        lbl_install_status = tk.Label(
            install_card,
            text="Status: Active (Strict Single-Instance Enforcement & In-Memory Execution)",
            font=("Segoe UI", 9)
        )
        lbl_install_status.pack(anchor="w", pady=(4, 12))
        themed_widgets["surface"].append(lbl_install_status)
        themed_widgets["text_dim"].append(lbl_install_status)

        inst_btn_row = tk.Frame(install_card)
        inst_btn_row.pack(anchor="w", pady=(0, 14))
        themed_widgets["surface"].append(inst_btn_row)

        def do_open_folder():
            p = os.getcwd()
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])

        btn_folder = PillButton(inst_btn_row, text="📂 OPEN APPLICATION FOLDER", command=do_open_folder, width=200, height=34, is_primary=True)
        btn_folder.pack(side=tk.LEFT)
        themed_widgets["pill_buttons"].append(btn_folder)

        info_text = (
            "• Single-Instance Guard: Strictly 1 instance permitted at a time (restores & focuses existing window)\n"
            "• Running Mode: Native Offline Client Application (Zero Network / No Localhost Required)\n"
            "• Scanning Architecture: In-Memory Multi-Threaded Telemetry Collector\n"
            "• Torture & Benchmarks: CPU torture, RAM pattern integrity check, disk throughput, thermal monitor\n"
            "• Storage Footprint: Standalone execution with zero registry pollution and zero installation files"
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

            for spark, container_key in themed_widgets.get("sparklines", []):
                try:
                    parent_bg = th[container_key] if container_key in th else th["card"]
                    spark.set_theme(
                        bg=parent_bg,
                        bar_color="#3b82f6" if self.current_theme == "dark" else "#2563eb",
                        bar_highlight="#60a5fa" if self.current_theme == "dark" else "#3b82f6"
                    )
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

            # ---------------------------------------------------------
            # Update Bento-Box Studio Cards
            # ---------------------------------------------------------
            # Hero Block: CPU Thermal & Boost Dynamics
            cpu_pkg_temp = getattr(report.cpu, "temperature_c", None)
            if cpu_pkg_temp is None:
                try:
                    th = audit_thermal_health(log_fn=None)
                    cpu_pkg_temp = float(th.get("cpu_temp_c", 58.0))
                except Exception:
                    cpu_pkg_temp = 58.0
            lbl_hero_temp.config(text=f"{int(round(cpu_pkg_temp))}")
            lbl_hero_clock.config(text=f"{report.cpu.model[:28]} • {format_hz(report.cpu.max_clock_mhz)} Boost")
            
            # Update sparkline with relative load/thermal fraction
            load_fraction = min(1.0, max(0.15, cpu_pkg_temp / 100.0))
            bento_sparkline.update_history(load_fraction)
            
            tjmax_delta = max(0.0, 100.0 - cpu_pkg_temp)
            lbl_hero_tjmax.config(text=f"TjMax Delta: {int(round(tjmax_delta))}°C Headroom")
            lbl_hero_badge.config(
                text="STABLE" if cpu_pkg_temp < 80 else ("WARM" if cpu_pkg_temp < 90 else "THROTTLED"),
                fg="#10b981" if cpu_pkg_temp < 80 else ("#f59e0b" if cpu_pkg_temp < 90 else "#ef4444")
            )

            # Bento Tile 1: Memory Allocation
            lbl_tmem_val.config(text=f"{format_bytes(report.memory.used_bytes)} / {format_bytes(report.memory.total_bytes)}")
            mem_pct = report.memory.percent / 100.0
            mem_bar_fill.place(x=0, y=0, relheight=1.0, relwidth=max(0.05, min(1.0, mem_pct)))

            # Bento Tile 2: SSD Health & TRIM
            free_pct = 32
            if report.storage.partitions:
                p0 = report.storage.partitions[0]
                free_pct = max(5, int(round((p0.free_bytes / max(1, p0.total_bytes)) * 100)))
            lbl_tssd_val.config(text=f"HEALTHY ({free_pct}% FREE)")

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
