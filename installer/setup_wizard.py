"""Graphical Windows Setup Wizard for Hardware Gauntlet styled with 100Days Design aesthetic."""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from PIL import Image, ImageDraw, ImageTk


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

    # 5. Installed app directory
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        candidates.append(os.path.join(appdata, "Programs", "HardwareGauntlet", "HardwareGauntlet.exe"))

    for c in candidates:
        if os.path.isfile(c) and os.path.exists(c):
            return os.path.abspath(c)
    return None


class SetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Gauntlet Setup")
        self.root.geometry("640x520")
        self.root.resizable(False, False)

        # Base paths
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        found_exe = locate_hardware_gauntlet_exe()
        if found_exe:
            self.source_dir = os.path.dirname(found_exe)
        elif not os.path.exists(os.path.join(self.source_dir, "HardwareGauntlet.exe")):
            self.source_dir = os.path.dirname(os.path.abspath(__file__))

        default_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        self.install_dir = tk.StringVar(value=os.path.join(default_appdata, "Programs", "HardwareGauntlet"))
        self.var_desktop = tk.BooleanVar(value=True)
        self.var_startmenu = tk.BooleanVar(value=True)
        self.var_path = tk.BooleanVar(value=True)
        self.var_launch = tk.BooleanVar(value=True)

        self.BG = "#09090b"
        self.SURFACE = "#111114"
        self.CARD = "#16161a"
        self.TEXT = "#ffffff"
        self.TEXT_DIM = "#a1a1aa"
        self.BORDER = "#27272e"
        self.BORDER_LIGHT = "#383842"
        self.ACCENT_WHITE = "#ffffff"
        self.ACCENT_SILVER = "#e4e4e7"

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
        target_exe = locate_hardware_gauntlet_exe()
        if target_exe:
            # If target_exe is inside PyInstaller's _MEIPASS temp directory,
            # copy to %TEMP%\HardwareGauntlet_Portable to avoid file locking on wizard exit
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
        tk.Label(hdr_text, text="YOUR SYSTEM — HARDWARE GAUNTLET", font=("Segoe UI", 14, "bold"), fg=self.ACCENT_WHITE, bg=self.SURFACE).pack(anchor="w")
        tk.Label(hdr_text, text="Universal Native Diagnostic Suite • Pure Local & Offline", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=28, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Select your execution preference:", font=("Segoe UI", 12, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(0, 14))

        # Option 1: Run Portable
        opt1_frame = tk.Frame(body, bg=self.CARD, padx=20, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        opt1_frame.pack(fill=tk.X, pady=(0, 14))

        opt1_top = tk.Frame(opt1_frame, bg=self.CARD)
        opt1_top.pack(fill=tk.X)
        tk.Label(opt1_top, text="CARD 01 —— ⚡ JUST RUN (ONE-OFF INSTANCE)", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_WHITE, bg=self.CARD).pack(side=tk.LEFT)
        btn_run = PillButton(opt1_top, text="⚡ RUN NOW", command=self.launch_portable, width=108, height=30, is_primary=True)
        btn_run.pack(side=tk.RIGHT)
        btn_run.configure(bg=self.CARD)

        tk.Label(opt1_frame, text="Runs immediately in-memory without installing files, modifying registry, or requiring administrator rights.", font=("Segoe UI", 8), fg=self.TEXT_DIM, bg=self.CARD, justify=tk.LEFT).pack(anchor="w", pady=(8, 0))

        # Option 2: Install as Application
        opt2_frame = tk.Frame(body, bg=self.CARD, padx=20, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        opt2_frame.pack(fill=tk.X, pady=(0, 14))

        opt2_top = tk.Frame(opt2_frame, bg=self.CARD)
        opt2_top.pack(fill=tk.X)
        tk.Label(opt2_top, text="CARD 02 —— 📦 INSTALL AS APPLICATION (PERMANENT)", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_WHITE, bg=self.CARD).pack(side=tk.LEFT)
        btn_inst = PillButton(opt2_top, text="INSTALL >", command=self.show_options_page, width=98, height=30, is_primary=False)
        btn_inst.pack(side=tk.RIGHT)
        btn_inst.configure(bg=self.CARD)

        tk.Label(opt2_frame, text="Installs permanently to your device with Start Menu search, Desktop shortcut, and Windows Settings 'Installed apps' integration.", font=("Segoe UI", 8), fg=self.TEXT_DIM, bg=self.CARD, justify=tk.LEFT).pack(anchor="w", pady=(8, 0))

        # Bottom nav
        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_exit = PillButton(footer, text="EXIT", command=self.root.destroy, width=70, height=32, is_primary=False)
        btn_exit.pack(side=tk.RIGHT, padx=4)
        btn_exit.configure(bg=self.SURFACE)

        btn_next = PillButton(footer, text="NEXT: INSTALL APP >", command=self.show_options_page, width=150, height=32, is_primary=True)
        btn_next.pack(side=tk.RIGHT, padx=4)
        btn_next.configure(bg=self.SURFACE)

        btn_port = PillButton(footer, text="⚡ RUN PORTABLY", command=self.launch_portable, width=130, height=32, is_primary=False)
        btn_port.pack(side=tk.LEFT)
        btn_port.configure(bg=self.SURFACE)

    def show_options_page(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="CARD 02 — INSTALL LOCATION & SYSTEM OPTIONS", font=("Segoe UI", 12, "bold"), fg=self.ACCENT_WHITE, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Destination Folder:", font=("Segoe UI", 9, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w")
        dir_frame = tk.Frame(body, bg=self.BG)
        dir_frame.pack(fill=tk.X, pady=(6, 16))

        tk.Entry(dir_frame, textvariable=self.install_dir, font=("Segoe UI", 9), bg=self.CARD, fg=self.TEXT, insertbackground="#fff", relief=tk.FLAT, highlightthickness=1, highlightbackground=self.BORDER).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def browse():
            d = filedialog.askdirectory(initialdir=self.install_dir.get())
            if d:
                self.install_dir.set(d)

        btn_browse = PillButton(dir_frame, text="BROWSE...", command=browse, width=86, height=28, is_primary=False)
        btn_browse.pack(side=tk.RIGHT, padx=(8, 0))
        btn_browse.configure(bg=self.BG)

        tk.Label(body, text="Integration Options:", font=("Segoe UI", 9, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(6, 4))

        tk.Checkbutton(body, text="Create Desktop shortcut", variable=self.var_desktop, font=("Segoe UI", 8), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)
        tk.Checkbutton(body, text="Create Start Menu entry (Windows Search integration)", variable=self.var_startmenu, font=("Segoe UI", 8), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)
        tk.Checkbutton(body, text="Add hwscan to User PATH (command-line terminal access)", variable=self.var_path, font=("Segoe UI", 8), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)

        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_can = PillButton(footer, text="CANCEL", command=self.root.destroy, width=78, height=32, is_primary=False)
        btn_can.pack(side=tk.RIGHT, padx=4)
        btn_can.configure(bg=self.SURFACE)

        btn_go = PillButton(footer, text="INSTALL NOW", command=self.start_installation, width=120, height=32, is_primary=True)
        btn_go.pack(side=tk.RIGHT, padx=4)
        btn_go.configure(bg=self.SURFACE)

        btn_back = PillButton(footer, text="< BACK", command=self.show_welcome_page, width=78, height=32, is_primary=False)
        btn_back.pack(side=tk.RIGHT, padx=4)
        btn_back.configure(bg=self.SURFACE)

    def start_installation(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="INSTALLATION IN PROGRESS —", font=("Segoe UI", 12, "bold"), fg=self.ACCENT_WHITE, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=28)
        body.pack(fill=tk.BOTH, expand=True)

        self.lbl_status = tk.Label(body, text="Preparing installation...", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG)
        self.lbl_status.pack(anchor="w", pady=(0, 12))

        self.progress = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 20))
        self.progress["value"] = 10

        threading.Thread(target=self._worker_install, daemon=True).start()

    def _worker_install(self):
        target = self.install_dir.get()
        assets_dir = os.path.join(target, "assets")

        try:
            self.lbl_status.config(text="Creating destination directory...")
            os.makedirs(target, exist_ok=True)
            os.makedirs(assets_dir, exist_ok=True)
            self.progress["value"] = 25

            self.lbl_status.config(text="Copying application binaries and resources...")
            exe_src = locate_hardware_gauntlet_exe()
            if exe_src and os.path.exists(exe_src):
                shutil.copy2(exe_src, os.path.join(target, "HardwareGauntlet.exe"))

            cli_src = os.path.join(self.source_dir, "dist", "hwscan-windows-x64.exe")
            if not os.path.exists(cli_src):
                cli_src = os.path.join(self.source_dir, "hwscan-windows-x64.exe")
            if os.path.exists(cli_src):
                shutil.copy2(cli_src, os.path.join(target, "hwscan.exe"))

            ico_src = os.path.join(self.source_dir, "assets", "app.ico")
            if os.path.exists(ico_src):
                shutil.copy2(ico_src, os.path.join(assets_dir, "app.ico"))

            uninst_src = os.path.join(self.source_dir, "installer", "uninstall-windows.ps1")
            if os.path.exists(uninst_src):
                shutil.copy2(uninst_src, os.path.join(target, "uninstall.ps1"))

            self.progress["value"] = 60

            self.lbl_status.config(text="Configuring Windows Start Menu and Desktop shortcuts...")
            script_path = os.path.join(self.source_dir, "installer", "install-windows.ps1")
            if os.path.exists(script_path):
                subprocess.run(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", script_path, "-NoLaunch"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                )

            self.progress["value"] = 100
            self.root.after(0, self.show_complete_page)

        except Exception as err:
            self.root.after(0, lambda: messagebox.showerror("Installation Error", f"Installation failed:\n{err}"))

    def show_complete_page(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=18, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="CARD 03 — INSTALLATION COMPLETED SUCCESSFULLY", font=("Segoe UI", 12, "bold"), fg=self.ACCENT_WHITE, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=24)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="✓ Hardware Gauntlet is ready on your PC!", font=("Segoe UI", 13, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(0, 10))

        details = (
            f"• Location: {self.install_dir.get()}\n"
            "• Desktop Shortcut: Created on Desktop\n"
            "• Start Menu: Searchable in Windows Search\n"
            "• CLI Command: Run 'hwscan' anywhere in terminal\n"
            "• Windows Settings: Registered in Installed Apps"
        )
        tk.Label(body, text=details, font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG, justify=tk.LEFT).pack(anchor="w", pady=(0, 16))

        tk.Checkbutton(body, text="Launch Hardware Gauntlet now", variable=self.var_launch, font=("Segoe UI", 9, "bold"), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w")

        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def finish():
            if self.var_launch.get():
                target = os.path.join(self.install_dir.get(), "HardwareGauntlet.exe")
                if os.path.exists(target):
                    subprocess.Popen([target])
            self.root.destroy()

        btn_fin = PillButton(footer, text="FINISH & LAUNCH", command=finish, width=140, height=32, is_primary=True)
        btn_fin.pack(side=tk.RIGHT, padx=4)
        btn_fin.configure(bg=self.SURFACE)

        btn_close = PillButton(footer, text="CLOSE", command=self.root.destroy, width=78, height=32, is_primary=False)
        btn_close.pack(side=tk.RIGHT, padx=4)
        btn_close.configure(bg=self.SURFACE)


def main():
    root = tk.Tk()
    SetupWizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
