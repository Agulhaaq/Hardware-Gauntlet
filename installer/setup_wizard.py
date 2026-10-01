"""Graphical Single-Instance Launcher for Hardware Gauntlet styled with 100Days Design aesthetic."""

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from PIL import Image, ImageDraw, ImageTk

from hwscan.core.installer_integration import find_existing_window, focus_window, WINDOW_TITLE


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
    """Pill-shaped capsule button with retina anti-aliasing matching 100Days design aesthetic."""

    def __init__(self, parent, text="BUTTON", command=None, width=120, height=32, is_primary=True, font=("Segoe UI", 8, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, cursor="hand2", **kwargs)
        self.text = text
        self.command = command
        self.w = width
        self.h = height
        self.is_primary = is_primary
        self.btn_font = font
        self.state = tk.NORMAL
        self.fill_color = "#ffffff" if is_primary else "#18181b"
        self.text_color = "#09090b" if is_primary else "#ffffff"
        self.hover_color = "#e4e4e7" if is_primary else "#27272a"
        self.border_color = "#ffffff" if is_primary else "#3f3f46"
        self._is_hovered = False

        self._img_norm: Optional[ImageTk.PhotoImage] = None
        self._img_hover: Optional[ImageTk.PhotoImage] = None
        self._img_disabled: Optional[ImageTk.PhotoImage] = None

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._bake_images()
        self.draw()

    def _bake_images(self):
        norm_raw = create_smooth_pill_img(self.w, self.h, self.fill_color, self.border_color if not self.is_primary else None)
        self._img_norm = ImageTk.PhotoImage(norm_raw)

        hover_raw = create_smooth_pill_img(self.w, self.h, self.hover_color, self.border_color if not self.is_primary else None)
        self._img_hover = ImageTk.PhotoImage(hover_raw)

        dis_raw = create_smooth_pill_img(self.w, self.h, "#27272a", None)
        self._img_disabled = ImageTk.PhotoImage(dis_raw)

    def set_text(self, new_text: str):
        self.text = new_text
        self.draw()

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

        if img:
            self.create_image(self.w / 2.0, self.h / 2.0, image=img)
        self.create_text(self.w / 2.0, self.h / 2.0, text=self.text, fill=t_col, font=self.btn_font)


def locate_hardware_gauntlet_exe() -> Optional[str]:
    """Find HardwareGauntlet.exe across bundled assets, executable dir, repo root, and temp."""
    candidates = []

    # 1. Next to current running executable
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "HardwareGauntlet.exe"))
    candidates.append(os.path.join(exe_dir, "dist", "HardwareGauntlet.exe"))

    # 2. PyInstaller bundle temp folder (_MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "HardwareGauntlet.exe"))
        candidates.append(os.path.join(sys._MEIPASS, "assets", "HardwareGauntlet.exe"))

    # 3. Project root / relative to __file__
    base_file = os.path.abspath(__file__)
    d1 = os.path.dirname(base_file)
    d2 = os.path.dirname(d1)
    candidates.append(os.path.join(d2, "HardwareGauntlet.exe"))
    candidates.append(os.path.join(d2, "dist", "HardwareGauntlet.exe"))
    candidates.append(os.path.join(d1, "HardwareGauntlet.exe"))

    # 4. Current working directory
    candidates.append(os.path.join(os.getcwd(), "HardwareGauntlet.exe"))
    candidates.append(os.path.join(os.getcwd(), "dist", "HardwareGauntlet.exe"))

    for c in candidates:
        if os.path.isfile(c) and os.path.exists(c):
            return os.path.abspath(c)
    return None


class SetupWizard:
    """Single-Instance Launcher for Hardware Gauntlet with 100Days design aesthetic."""

    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Gauntlet — Single Instance Launcher")
        self.root.geometry("600x420")
        self.root.resizable(False, False)

        # Base paths
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        found_exe = locate_hardware_gauntlet_exe()
        if found_exe:
            self.source_dir = os.path.dirname(found_exe)
        elif not os.path.exists(os.path.join(self.source_dir, "HardwareGauntlet.exe")):
            self.source_dir = os.path.dirname(os.path.abspath(__file__))

        self.BG = "#09090b"
        self.SURFACE = "#111114"
        self.CARD = "#16161a"
        self.TEXT = "#ffffff"
        self.TEXT_DIM = "#a1a1aa"
        self.BORDER = "#27272e"
        self.ACCENT_WHITE = "#ffffff"

        self.root.configure(bg=self.BG)

        ico_path = os.path.join(self.source_dir, "assets", "app.ico")
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        self.container = tk.Frame(root, bg=self.BG)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.show_welcome_page()

    def clear_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def launch_portable(self):
        """Ensure single instance: focus existing instance or launch the standalone application."""
        hwnd = find_existing_window(WINDOW_TITLE)
        if hwnd:
            focus_window(hwnd)
            self.root.destroy()
            return

        target_exe = locate_hardware_gauntlet_exe()
        if target_exe:
            # If target_exe is inside PyInstaller's _MEIPASS temp directory, copy to portable dir
            if hasattr(sys, "_MEIPASS") and target_exe.startswith(sys._MEIPASS):
                import tempfile
                temp_run_dir = os.path.join(tempfile.gettempdir(), "HardwareGauntlet_Portable")
                os.makedirs(temp_run_dir, exist_ok=True)
                portable_exe = os.path.join(temp_run_dir, "HardwareGauntlet.exe")
                try:
                    shutil.copy2(target_exe, portable_exe)
                    target_exe = portable_exe
                except Exception:
                    pass

            run_cwd = os.path.dirname(target_exe)
            subprocess.Popen([target_exe], cwd=run_cwd)
            self.root.destroy()
            return

        gui_py = os.path.join(self.source_dir, "hwscan", "gui.py")
        if os.path.exists(gui_py):
            subprocess.Popen([sys.executable, "-m", "hwscan.gui"], cwd=self.source_dir)
            self.root.destroy()
            return

        messagebox.showerror(
            "Executable Not Found",
            "HardwareGauntlet.exe could not be located.\n\nPlease ensure HardwareGauntlet.exe is in the application folder."
        )

    def show_welcome_page(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=18, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)

        logo_path = os.path.join(self.source_dir, "assets", "logo_white_48.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(self.source_dir, "assets", "logo_white.png")
        if os.path.exists(logo_path):
            try:
                self._hdr_logo = tk.PhotoImage(file=logo_path)
                tk.Label(hdr, image=self._hdr_logo, bg=self.SURFACE).pack(side=tk.LEFT, padx=(0, 14))
            except Exception:
                pass

        hdr_text = tk.Frame(hdr, bg=self.SURFACE)
        hdr_text.pack(side=tk.LEFT)
        tk.Label(hdr_text, text="YOUR SYSTEM — HARDWARE GAUNTLET", font=("Segoe UI", 13, "bold"), fg=self.ACCENT_WHITE, bg=self.SURFACE).pack(anchor="w")
        tk.Label(hdr_text, text="Strict Single-Instance Diagnostic Suite • Pure Local & Offline", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=28, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        # Card 01: Run Single Instance
        opt1_frame = tk.Frame(body, bg=self.CARD, padx=20, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        opt1_frame.pack(fill=tk.X, pady=(0, 14))

        opt1_top = tk.Frame(opt1_frame, bg=self.CARD)
        opt1_top.pack(fill=tk.X)
        tk.Label(opt1_top, text="CARD 01 —— ⚡ RUN APPLICATION (SINGLE INSTANCE)", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_WHITE, bg=self.CARD).pack(side=tk.LEFT)
        btn_run = PillButton(opt1_top, text="⚡ RUN NOW", command=self.launch_portable, width=108, height=30, is_primary=True)
        btn_run.pack(side=tk.RIGHT)
        btn_run.configure(bg=self.CARD)

        tk.Label(
            opt1_frame,
            text="Launches Hardware Gauntlet immediately. If an instance is already running, it brings that instance directly to the front.",
            font=("Segoe UI", 8),
            fg=self.TEXT_DIM,
            bg=self.CARD,
            justify=tk.LEFT
        ).pack(anchor="w", pady=(8, 0))

        # Card 02: Architecture & Runtime Details
        opt2_frame = tk.Frame(body, bg=self.CARD, padx=20, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        opt2_frame.pack(fill=tk.X)

        tk.Label(opt2_frame, text="CARD 02 —— 🔒 SINGLE-INSTANCE & LOCAL INTEGRITY", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_WHITE, bg=self.CARD).pack(anchor="w")
        details_txt = (
            "• Single-Instance Guard: Only 1 application window is permitted at a time\n"
            "• Zero Installation Footprint: Pure in-memory standalone execution without system mutation\n"
            "• Offline & Sandboxed: 100% private, zero network telemetry or tracking"
        )
        tk.Label(opt2_frame, text=details_txt, font=("Segoe UI", 8), fg=self.TEXT_DIM, bg=self.CARD, justify=tk.LEFT).pack(anchor="w", pady=(8, 0))

        # Bottom nav
        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_exit = PillButton(footer, text="EXIT", command=self.root.destroy, width=70, height=32, is_primary=False)
        btn_exit.pack(side=tk.RIGHT, padx=4)
        btn_exit.configure(bg=self.SURFACE)

        btn_launch = PillButton(footer, text="⚡ LAUNCH INSTANCE", command=self.launch_portable, width=160, height=32, is_primary=True)
        btn_launch.pack(side=tk.RIGHT, padx=4)
        btn_launch.configure(bg=self.SURFACE)


# Alias for backward compatibility
SingleInstanceLauncher = SetupWizard


def main():
    # If Hardware Gauntlet is already running, focus it and exit immediately
    hwnd = find_existing_window(WINDOW_TITLE)
    if hwnd:
        focus_window(hwnd)
        print("[*] Hardware Gauntlet is already running. Focus transferred to active window.")
        return

    root = tk.Tk()
    SetupWizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
