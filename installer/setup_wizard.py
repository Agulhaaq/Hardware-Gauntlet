"""Graphical Windows Setup Wizard for Hardware Gauntlet."""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class SetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Gauntlet Setup")
        self.root.geometry("640x500")
        self.root.resizable(False, False)

        # Base paths
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists(os.path.join(self.source_dir, "HardwareGauntlet.exe")):
            self.source_dir = os.path.dirname(os.path.abspath(__file__))

        default_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        self.install_dir = tk.StringVar(value=os.path.join(default_appdata, "Programs", "HardwareGauntlet"))
        self.var_desktop = tk.BooleanVar(value=True)
        self.var_startmenu = tk.BooleanVar(value=True)
        self.var_path = tk.BooleanVar(value=True)
        self.var_launch = tk.BooleanVar(value=True)

        # Dark theme colors
        self.BG = "#0b0f19"
        self.SURFACE = "#111827"
        self.CARD = "#1e293b"
        self.TEXT = "#f8fafc"
        self.TEXT_DIM = "#94a3b8"
        self.CYAN = "#38bdf8"
        self.GREEN = "#10b981"
        self.BORDER = "#334155"

        self.root.configure(bg=self.BG)

        # Set window icon
        ico_path = os.path.join(self.source_dir, "assets", "app.ico")
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # Container for pages
        self.container = tk.Frame(root, bg=self.BG)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.show_welcome_page()

    def clear_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def launch_portable(self):
        target_exe = os.path.join(self.source_dir, "HardwareGauntlet.exe")
        if os.path.exists(target_exe):
            subprocess.Popen([target_exe], cwd=self.source_dir)
            self.root.destroy()
            return
        gui_py = os.path.join(self.source_dir, "hwscan", "gui.py")
        if os.path.exists(gui_py):
            subprocess.Popen([sys.executable, "-m", "hwscan.gui"], cwd=self.source_dir)
            self.root.destroy()
            return
        messagebox.showerror("Error", f"Executable not found at:\n{target_exe}")

    def show_welcome_page(self):
        self.clear_page()

        # Header banner
        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=18, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="⚡ Hardware Gauntlet", font=("Segoe UI", 16, "bold"), fg=self.CYAN, bg=self.SURFACE).pack(anchor="w")
        tk.Label(hdr, text="Universal Native Hardware Diagnostic Suite - Pure Local & Offline", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=28, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="How would you like to run Hardware Gauntlet?", font=("Segoe UI", 13, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(0, 14))

        # Option 1: Run Portable (One-off instance)
        opt1_frame = tk.Frame(body, bg=self.CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        opt1_frame.pack(fill=tk.X, pady=(0, 12))

        opt1_top = tk.Frame(opt1_frame, bg=self.CARD)
        opt1_top.pack(fill=tk.X)
        tk.Label(opt1_top, text="⚡ Just Run (One-Off Portable Instance)", font=("Segoe UI", 11, "bold"), fg=self.CYAN, bg=self.CARD).pack(side=tk.LEFT)
        tk.Button(opt1_top, text="Run Now 🚀", command=self.launch_portable, font=("Segoe UI", 9, "bold"), bg="#0284c7", fg="#ffffff", relief=tk.FLAT, padx=14, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        tk.Label(opt1_frame, text="Runs immediately in-memory without installing files, modifying registry, or requiring administrator rights.", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.CARD, justify=tk.LEFT).pack(anchor="w", pady=(6, 0))

        # Option 2: Install as Application
        opt2_frame = tk.Frame(body, bg=self.CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        opt2_frame.pack(fill=tk.X, pady=(0, 12))

        opt2_top = tk.Frame(opt2_frame, bg=self.CARD)
        opt2_top.pack(fill=tk.X)
        tk.Label(opt2_top, text="📦 Install as Application (Permanent Setup)", font=("Segoe UI", 11, "bold"), fg=self.GREEN, bg=self.CARD).pack(side=tk.LEFT)
        tk.Button(opt2_top, text="Install >", command=self.show_options_page, font=("Segoe UI", 9, "bold"), bg="#16a34a", fg="#ffffff", relief=tk.FLAT, padx=16, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        tk.Label(opt2_frame, text="Installs permanently to your device with Start Menu search, Desktop shortcut, and Windows Settings 'Installed apps' integration.", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.CARD, justify=tk.LEFT).pack(anchor="w", pady=(6, 0))

        # Bottom nav
        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Button(footer, text="Exit", command=self.root.destroy, font=("Segoe UI", 9), bg=self.CARD, fg=self.TEXT, relief=tk.FLAT, padx=16, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)
        tk.Button(footer, text="⚡ Just Run Now", command=self.launch_portable, font=("Segoe UI", 9, "bold"), bg=self.CARD, fg=self.CYAN, relief=tk.FLAT, padx=14, pady=6, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(footer, text="Next: Install App >", command=self.show_options_page, font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", relief=tk.FLAT, padx=16, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)

    def show_options_page(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Choose Install Location & Options", font=("Segoe UI", 14, "bold"), fg=self.CYAN, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Destination Folder:", font=("Segoe UI", 10, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w")
        dir_frame = tk.Frame(body, bg=self.BG)
        dir_frame.pack(fill=tk.X, pady=(6, 16))

        tk.Entry(dir_frame, textvariable=self.install_dir, font=("Segoe UI", 9), bg=self.CARD, fg=self.TEXT, insertbackground="#fff", relief=tk.FLAT).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        def browse():
            d = filedialog.askdirectory(initialdir=self.install_dir.get())
            if d:
                self.install_dir.set(d)

        tk.Button(dir_frame, text="Browse...", command=browse, font=("Segoe UI", 8), bg=self.CARD, fg=self.CYAN, relief=tk.FLAT, padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(body, text="Integration Options:", font=("Segoe UI", 10, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(8, 6))

        tk.Checkbutton(body, text="Create Desktop shortcut", variable=self.var_desktop, font=("Segoe UI", 9), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)
        tk.Checkbutton(body, text="Create Start Menu entry (Windows Search integration)", variable=self.var_startmenu, font=("Segoe UI", 9), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)
        tk.Checkbutton(body, text="Add hwscan to User PATH (command-line terminal access)", variable=self.var_path, font=("Segoe UI", 9), fg=self.TEXT, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.TEXT).pack(anchor="w", pady=2)

        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Button(footer, text="Cancel", command=self.root.destroy, font=("Segoe UI", 9), bg=self.CARD, fg=self.TEXT, relief=tk.FLAT, padx=14, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)
        tk.Button(footer, text="Install Now", command=self.start_installation, font=("Segoe UI", 9, "bold"), bg=self.GREEN, fg="#000000", relief=tk.FLAT, padx=16, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)
        tk.Button(footer, text="< Back", command=self.show_welcome_page, font=("Segoe UI", 9), bg=self.CARD, fg=self.TEXT, relief=tk.FLAT, padx=14, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)

    def start_installation(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=16, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Installing Hardware Gauntlet...", font=("Segoe UI", 14, "bold"), fg=self.CYAN, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=28)
        body.pack(fill=tk.BOTH, expand=True)

        self.lbl_status = tk.Label(body, text="Preparing installation...", font=("Segoe UI", 10), fg=self.TEXT_DIM, bg=self.BG)
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
            exe_src = os.path.join(self.source_dir, "HardwareGauntlet.exe")
            if os.path.exists(exe_src):
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

            # Shortcuts and registry via powershell
            self.lbl_status.config(text="Configuring Windows Start Menu and Desktop shortcuts...")
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $TargetExe = "{target}\\HardwareGauntlet.exe"
            $IconFile = "{assets_dir}\\app.ico"

            if ("{str(self.var_startmenu.get()).lower()}" -eq "true") {{
                $StartLnk = "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Hardware Gauntlet.lnk"
                $s = $WshShell.CreateShortcut($StartLnk)
                $s.TargetPath = $TargetExe
                $s.WorkingDirectory = "{target}"
                $s.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
                if (Test-Path $IconFile) {{ $s.IconLocation = "$IconFile,0" }}
                $s.Save()
            }}

            if ("{str(self.var_desktop.get()).lower()}" -eq "true") {{
                $DesktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Hardware Gauntlet.lnk")
                $d = $WshShell.CreateShortcut($DesktopLnk)
                $d.TargetPath = $TargetExe
                $d.WorkingDirectory = "{target}"
                $d.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
                if (Test-Path $IconFile) {{ $d.IconLocation = "$IconFile,0" }}
                $d.Save()
            }}

            # Registry entry for Installed Apps
            $RegKey = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\HardwareGauntlet"
            New-Item -Path $RegKey -Force | Out-Null
            Set-ItemProperty -Path $RegKey -Name "DisplayName" -Value "Hardware Gauntlet"
            Set-ItemProperty -Path $RegKey -Name "DisplayVersion" -Value "1.0.0"
            Set-ItemProperty -Path $RegKey -Name "Publisher" -Value "Hardware Gauntlet Team"
            Set-ItemProperty -Path $RegKey -Name "InstallLocation" -Value "{target}"
            Set-ItemProperty -Path $RegKey -Name "DisplayIcon" -Value "$IconFile"
            Set-ItemProperty -Path $RegKey -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"{target}\\uninstall.ps1`""
            Set-ItemProperty -Path $RegKey -Name "EstimatedSize" -Value 41000

            if ("{str(self.var_path.get()).lower()}" -eq "true") {{
                $userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
                if ($userPath -notlike "*{target}*") {{
                    [Environment]::SetEnvironmentVariable("Path", "$userPath;{target}", [EnvironmentVariableTarget]::User)
                }}
            }}
            """
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script], check=False)

            self.progress["value"] = 100
            self.root.after(300, self.show_completed_page)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Installation Error", f"Installation failed:\n{e}"))

    def show_completed_page(self):
        self.clear_page()

        hdr = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=20, highlightthickness=1, highlightbackground=self.BORDER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="✓ Installation Completed!", font=("Segoe UI", 16, "bold"), fg=self.GREEN, bg=self.SURFACE).pack(anchor="w")

        body = tk.Frame(self.container, bg=self.BG, padx=32, pady=24)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Hardware Gauntlet has been installed successfully!", font=("Segoe UI", 12, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", pady=(0, 10))
        tk.Label(body, text=f"Installed Location:\n{self.install_dir.get()}\n\nYou can launch Hardware Gauntlet anytime from your Start Menu or Desktop.", font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG, justify=tk.LEFT).pack(anchor="w", pady=(0, 16))

        tk.Checkbutton(body, text="Launch Hardware Gauntlet now", variable=self.var_launch, font=("Segoe UI", 10, "bold"), fg=self.CYAN, bg=self.BG, selectcolor=self.CARD, activebackground=self.BG, activeforeground=self.CYAN).pack(anchor="w")

        footer = tk.Frame(self.container, bg=self.SURFACE, padx=24, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def finish():
            if self.var_launch.get():
                target_exe = os.path.join(self.install_dir.get(), "HardwareGauntlet.exe")
                if os.path.exists(target_exe):
                    subprocess.Popen([target_exe])
            self.root.destroy()

        tk.Button(footer, text="Finish", command=finish, font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)


if __name__ == "__main__":
    root = tk.Tk()
    app = SetupWizard(root)
    root.mainloop()
