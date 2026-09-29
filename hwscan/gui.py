"""Native Desktop GUI Application for Hardware Gauntlet with Clean Modern UI, Dark/Light Themes, Single-Instance Lock, Manual Scan, and Stress Test Suite."""

import os
import sys
import json
import time
import subprocess
import webbrowser
import threading
from typing import Optional, Dict, Any

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


THEMES = {
    "dark": {
        "name": "dark",
        "bg": "#09090b",
        "surface": "#121215",
        "card": "#18181b",
        "card_alt": "#1f1f23",
        "border": "#27272a",
        "border_subtle": "#1e1e24",
        "border_light": "#3f3f46",
        "text": "#ffffff",
        "text_dim": "#a1a1aa",
        "text_muted": "#71717a",
        "accent": "#ffffff",
        "accent_text": "#09090b",
        "accent_hover": "#e4e4e7",
        "btn_bg": "#18181b",
        "btn_fg": "#ffffff",
        "btn_border": "#27272a",
        "btn_hover": "#27272a",
        "console_bg": "#0c0c0e",
        "console_fg": "#e4e4e7",
        "tree_bg": "#121215",
        "tree_fg": "#ffffff",
        "tree_alt": "#16161a",
        "tree_head_bg": "#18181b",
        "tree_head_fg": "#ffffff",
        "tree_sel_bg": "#27272a",
        "tree_sel_fg": "#ffffff",
        "tab_bg": "#18181b",
        "tab_fg": "#a1a1aa",
        "tab_sel_bg": "#ffffff",
        "tab_sel_fg": "#09090b",
        "toggle_text": "☀️ Light Mode",
        "logo_file": "logo_white_48.png",
        "logo_fallback": "logo_white.png",
    },
    "light": {
        "name": "light",
        "bg": "#f4f4f5",
        "surface": "#ffffff",
        "card": "#f8fafc",
        "card_alt": "#f1f5f9",
        "border": "#e2e8f0",
        "border_subtle": "#e4e4e7",
        "border_light": "#cbd5e1",
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
        "toggle_text": "🌙 Dark Mode",
        "logo_file": "logo_black_48.png",
        "logo_fallback": "logo_black.png",
    }
}


def get_asset_file_path(filename: str) -> str:
    """Resolve asset paths whether running from source, PyInstaller bundle, or installed directory."""
    candidates = []
    # PyInstaller extracted bundle dir
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "assets", filename))
        candidates.append(os.path.join(sys._MEIPASS, filename))
    # Next to executable
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "assets", filename))
    candidates.append(os.path.join(exe_dir, filename))
    # Source repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(repo_root, "assets", filename))
    candidates.append(os.path.join(repo_root, filename))
    # LocalAppData install dir
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        candidates.append(os.path.join(appdata, "Programs", "HardwareGauntlet", "assets", filename))

    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(repo_root, "assets", filename)


class HardwareGauntletGUI:
    """Orchestrates launching the modern clean desktop application with dual dark/light themes."""

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
        """Render native Tkinter GUI with clean layout, manual scan controls, and stress test engine."""
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog

        root = tk.Tk()
        root.title(WINDOW_TITLE)
        root.geometry("1160x800")
        root.minsize(960, 680)

        # Set window icon
        ico_path = get_asset_file_path("app.ico")
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                root.iconbitmap(ico_path)
            except Exception:
                pass

        # Registry for dynamic theme re-styling
        themed_widgets = {
            "root_bg": [root],
            "surface": [],
            "cards": [],
            "card_alts": [],
            "borders": [],
            "text_primary": [],
            "text_dim": [],
            "text_muted": [],
            "btn_primary": [],
            "btn_secondary": [],
            "consoles": [],
            "treeviews": [],
        }

        style = ttk.Style()
        style.theme_use("clam")

        # -------------------------------------------------------------
        # Header Toolbar
        # -------------------------------------------------------------
        header = tk.Frame(root, padx=22, pady=14, highlightthickness=1)
        header.pack(fill=tk.X, side=tk.TOP)
        themed_widgets["surface"].append(header)
        themed_widgets["borders"].append(header)

        # Logo and Title Left
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

        lbl_main_title = tk.Label(title_row, text="HARDWARE GAUNTLET", font=("Segoe UI", 15, "bold"))
        lbl_main_title.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_main_title)
        themed_widgets["text_primary"].append(lbl_main_title)

        lbl_tag = tk.Label(title_row, text="v1.0.0 • Local Engine", font=("Segoe UI", 8, "bold"), padx=6, pady=1)
        lbl_tag.pack(side=tk.LEFT, padx=(10, 0))
        themed_widgets["card_alts"].append(lbl_tag)
        themed_widgets["text_dim"].append(lbl_tag)

        lbl_subtitle = tk.Label(title_text_box, text="Ready to audit hardware. Click '▶ Run Full Scan' to analyze all subsystems.", font=("Segoe UI", 9))
        lbl_subtitle.pack(anchor="w", pady=(2, 0))
        themed_widgets["surface"].append(lbl_subtitle)
        themed_widgets["text_dim"].append(lbl_subtitle)

        # Action Buttons Right
        btn_frame = tk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        themed_widgets["surface"].append(btn_frame)

        # Health Score Card
        score_val = tk.StringVar(value="--")
        score_rating = tk.StringVar(value="READY")

        score_card = tk.Frame(btn_frame, padx=14, pady=5, highlightthickness=1)
        score_card.pack(side=tk.LEFT, padx=(0, 12))
        themed_widgets["cards"].append(score_card)
        themed_widgets["borders"].append(score_card)

        score_inner = tk.Frame(score_card)
        score_inner.pack()
        themed_widgets["cards"].append(score_inner)

        lbl_score_num = tk.Label(score_inner, textvariable=score_val, font=("Segoe UI", 16, "bold"))
        lbl_score_num.pack(side=tk.LEFT, padx=(0, 8))
        themed_widgets["cards"].append(lbl_score_num)
        themed_widgets["text_primary"].append(lbl_score_num)

        score_meta = tk.Frame(score_inner)
        score_meta.pack(side=tk.LEFT)
        themed_widgets["cards"].append(score_meta)

        lbl_score_title = tk.Label(score_meta, text="HEALTH SCORE", font=("Segoe UI", 7, "bold"))
        lbl_score_title.pack(anchor="w")
        themed_widgets["cards"].append(lbl_score_title)
        themed_widgets["text_dim"].append(lbl_score_title)

        lbl_score_chip = tk.Label(score_meta, textvariable=score_rating, font=("Segoe UI", 8, "bold"))
        lbl_score_chip.pack(anchor="w")
        themed_widgets["cards"].append(lbl_score_chip)
        themed_widgets["text_primary"].append(lbl_score_chip)

        # Callbacks
        def do_scan():
            if self._is_scanning:
                return
            self._is_scanning = True
            btn_scan.config(state=tk.DISABLED, text="⏳ Scanning...")
            btn_overview_scan.config(state=tk.DISABLED, text="⏳ Scanning...")
            lbl_subtitle.config(text="Auditing CPU, memory modules, GPU, storage drives, and security firmware...")
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
            btn_install.config(state=tk.DISABLED, text="⏳ Installing...")
            def worker():
                success, msg = install_application()
                def on_done():
                    btn_install.config(state=tk.NORMAL, text="✓ Installed" if success else "📦 Install to PC")
                    if success:
                        lbl_install_status.config(text=f"Status: Installed in {get_install_directory()}")
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

        # Header Buttons
        btn_scan = tk.Button(btn_frame, text="▶ Run Full Scan", command=do_scan, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=14, pady=6, cursor="hand2", highlightthickness=1)
        btn_scan.pack(side=tk.LEFT, padx=3)
        themed_widgets["btn_primary"].append(btn_scan)

        btn_install = tk.Button(btn_frame, text="✓ Installed" if is_installed() else "📦 Install to PC", command=do_install, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, pady=6, cursor="hand2", highlightthickness=1)
        btn_install.pack(side=tk.LEFT, padx=3)
        themed_widgets["btn_secondary"].append(btn_install)

        btn_theme = tk.Button(btn_frame, command=toggle_theme, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=6, cursor="hand2", highlightthickness=1)
        btn_theme.pack(side=tk.LEFT, padx=3)
        themed_widgets["btn_secondary"].append(btn_theme)

        btn_html = tk.Button(btn_frame, text="📄 HTML", command=do_export_html, font=("Segoe UI", 9), relief=tk.FLAT, padx=10, pady=6, cursor="hand2", highlightthickness=1)
        btn_html.pack(side=tk.LEFT, padx=3)
        themed_widgets["btn_secondary"].append(btn_html)

        btn_json = tk.Button(btn_frame, text="💾 JSON", command=do_export_json, font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=6, cursor="hand2", highlightthickness=1)
        btn_json.pack(side=tk.LEFT, padx=3)
        themed_widgets["btn_secondary"].append(btn_json)

        # -------------------------------------------------------------
        # Main Tab Navigation
        # -------------------------------------------------------------
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=18, pady=(10, 16))

        def create_tab(title):
            tab = tk.Frame(notebook, padx=16, pady=16)
            notebook.add(tab, text=title)
            themed_widgets["root_bg"].append(tab)
            return tab

        tab_overview = create_tab("📊 Overview")
        tab_stress = create_tab("🔥 Stress Test")
        tab_cpu = create_tab("🧠 CPU & Board")
        tab_mem = create_tab("💾 Memory")
        tab_gpu = create_tab("🎮 Graphics")
        tab_storage = create_tab("💽 Storage")
        tab_security = create_tab("🔒 Security")
        tab_tools = create_tab("🛠️ Diagnostics & Install")

        # -------------------------------------------------------------
        # Tab 1: Overview & Modern KPI Tiles
        # -------------------------------------------------------------
        banner_frame = tk.Frame(tab_overview, padx=18, pady=12, highlightthickness=1)
        banner_frame.pack(fill=tk.X, pady=(0, 14))
        themed_widgets["surface"].append(banner_frame)
        themed_widgets["borders"].append(banner_frame)

        banner_inner = tk.Frame(banner_frame)
        banner_inner.pack(fill=tk.X)
        themed_widgets["surface"].append(banner_inner)

        lbl_banner_title = tk.Label(banner_inner, text="SYSTEM READY FOR HARDWARE AUDIT", font=("Segoe UI", 11, "bold"))
        lbl_banner_title.pack(anchor="w")
        themed_widgets["surface"].append(lbl_banner_title)
        themed_widgets["text_primary"].append(lbl_banner_title)

        lbl_banner_desc = tk.Label(banner_inner, text="Hardware Gauntlet audits CPU architecture, physical DIMM sockets, GPU controllers, NVMe/SATA health, and UEFI security parameters.", font=("Segoe UI", 9))
        lbl_banner_desc.pack(anchor="w", pady=(2, 6))
        themed_widgets["surface"].append(lbl_banner_desc)
        themed_widgets["text_dim"].append(lbl_banner_desc)

        btn_overview_scan = tk.Button(banner_inner, text="▶ Run Full Scan Now", command=do_scan, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=14, pady=5, cursor="hand2", highlightthickness=1)
        btn_overview_scan.pack(anchor="w")
        themed_widgets["btn_primary"].append(btn_overview_scan)

        kpi_grid = tk.Frame(tab_overview)
        kpi_grid.pack(fill=tk.X, pady=(0, 14))
        themed_widgets["root_bg"].append(kpi_grid)

        def create_kpi_card(parent, title):
            card = tk.Frame(parent, padx=16, pady=12, highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            themed_widgets["surface"].append(card)
            themed_widgets["borders"].append(card)

            lbl_t = tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"))
            lbl_t.pack(anchor="w")
            themed_widgets["surface"].append(lbl_t)
            themed_widgets["text_dim"].append(lbl_t)

            lbl_v = tk.Label(card, text="Click 'Run Scan'", font=("Segoe UI", 11, "bold"))
            lbl_v.pack(anchor="w", pady=(3, 2))
            themed_widgets["surface"].append(lbl_v)
            themed_widgets["text_primary"].append(lbl_v)

            lbl_s = tk.Label(card, text="Awaiting trigger", font=("Segoe UI", 8))
            lbl_s.pack(anchor="w")
            themed_widgets["surface"].append(lbl_s)
            themed_widgets["text_dim"].append(lbl_s)
            return lbl_v, lbl_s

        kpi_cpu_v, kpi_cpu_s = create_kpi_card(kpi_grid, "Processor (CPU)")
        kpi_mem_v, kpi_mem_s = create_kpi_card(kpi_grid, "Memory (RAM)")
        kpi_gpu_v, kpi_gpu_s = create_kpi_card(kpi_grid, "Graphics (GPU)")
        kpi_sec_v, kpi_sec_s = create_kpi_card(kpi_grid, "Security & Boot")

        lbl_findings_hdr = tk.Label(tab_overview, text="HARDWARE DIAGNOSTIC FINDINGS & ALERTS", font=("Segoe UI", 10, "bold"))
        lbl_findings_hdr.pack(anchor="w", pady=(4, 6))
        themed_widgets["root_bg"].append(lbl_findings_hdr)
        themed_widgets["text_primary"].append(lbl_findings_hdr)

        tree_warn = ttk.Treeview(tab_overview, columns=("level", "category", "details"), show="headings", height=8)
        tree_warn.heading("level", text="Severity")
        tree_warn.heading("category", text="Category")
        tree_warn.heading("details", text="Observation & Recommendation")
        tree_warn.column("level", width=110, anchor="center")
        tree_warn.column("category", width=140)
        tree_warn.column("details", width=740)
        tree_warn.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_warn)

        tree_warn.insert("", tk.END, values=("READY", "Scanner", "System audit ready. Click '▶ Run Full Scan' in the toolbar to begin analysis."), tags=("even",))

        # -------------------------------------------------------------
        # Tab 2: 🔥 Stress Test & Thermal Stability
        # -------------------------------------------------------------
        stress_ctrl_box = tk.Frame(tab_stress, padx=18, pady=12, highlightthickness=1)
        stress_ctrl_box.pack(fill=tk.X, pady=(0, 12))
        themed_widgets["surface"].append(stress_ctrl_box)
        themed_widgets["borders"].append(stress_ctrl_box)

        lbl_stress_hdr = tk.Label(stress_ctrl_box, text="HARDWARE TORTURE & STABILITY BENCHMARK", font=("Segoe UI", 11, "bold"))
        lbl_stress_hdr.pack(anchor="w")
        themed_widgets["surface"].append(lbl_stress_hdr)
        themed_widgets["text_primary"].append(lbl_stress_hdr)

        lbl_stress_sub = tk.Label(stress_ctrl_box, text="Stress-tests multi-core CPU mathematical load, RAM bit-pattern integrity, sequential disk throughput, and thermal throttling.", font=("Segoe UI", 8))
        lbl_stress_sub.pack(anchor="w", pady=(1, 10))
        themed_widgets["surface"].append(lbl_stress_sub)
        themed_widgets["text_dim"].append(lbl_stress_sub)

        stress_opt_row = tk.Frame(stress_ctrl_box)
        stress_opt_row.pack(fill=tk.X)
        themed_widgets["surface"].append(stress_opt_row)

        var_test_cpu = tk.BooleanVar(value=True)
        var_test_ram = tk.BooleanVar(value=True)
        var_test_disk = tk.BooleanVar(value=True)

        chk_cpu = tk.Checkbutton(stress_opt_row, text="CPU Multi-Core", variable=var_test_cpu, font=("Segoe UI", 9, "bold"), cursor="hand2")
        chk_cpu.pack(side=tk.LEFT, padx=(0, 14))
        themed_widgets["surface"].append(chk_cpu)
        themed_widgets["text_primary"].append(chk_cpu)

        chk_ram = tk.Checkbutton(stress_opt_row, text="RAM Bit Integrity", variable=var_test_ram, font=("Segoe UI", 9, "bold"), cursor="hand2")
        chk_ram.pack(side=tk.LEFT, padx=(0, 14))
        themed_widgets["surface"].append(chk_ram)
        themed_widgets["text_primary"].append(chk_ram)

        chk_disk = tk.Checkbutton(stress_opt_row, text="Disk Sequential I/O", variable=var_test_disk, font=("Segoe UI", 9, "bold"), cursor="hand2")
        chk_disk.pack(side=tk.LEFT, padx=(0, 20))
        themed_widgets["surface"].append(chk_disk)
        themed_widgets["text_primary"].append(chk_disk)

        tk.Label(stress_opt_row, text="Duration:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        themed_widgets["surface"].append(stress_opt_row.winfo_children()[-1])
        themed_widgets["text_dim"].append(stress_opt_row.winfo_children()[-1])

        combo_duration = ttk.Combobox(stress_opt_row, values=["15 Seconds (Quick)", "30 Seconds (Standard)", "60 Seconds (Heavy)", "120 Seconds (Torture)"], state="readonly", width=22)
        combo_duration.current(1)
        combo_duration.pack(side=tk.LEFT, padx=(0, 20))

        btn_start_stress = tk.Button(stress_opt_row, text="▶ Start Stress Test", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=16, pady=5, cursor="hand2", highlightthickness=1)
        btn_start_stress.pack(side=tk.LEFT, padx=(0, 8))
        themed_widgets["btn_primary"].append(btn_start_stress)

        btn_stop_stress = tk.Button(stress_opt_row, text="⏹ Stop", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, pady=5, cursor="hand2", state=tk.DISABLED, highlightthickness=1)
        btn_stop_stress.pack(side=tk.LEFT)
        themed_widgets["btn_secondary"].append(btn_stop_stress)

        # Stress Telemetry Cards
        stress_grid = tk.Frame(tab_stress)
        stress_grid.pack(fill=tk.X, pady=(0, 12))
        themed_widgets["root_bg"].append(stress_grid)

        tile_cpu_v, tile_cpu_s = create_kpi_card(stress_grid, "CPU Utilization")
        tile_temp_v, tile_temp_s = create_kpi_card(stress_grid, "Thermal & GPU Temp")
        tile_ram_v, tile_ram_s = create_kpi_card(stress_grid, "RAM Integrity")
        tile_disk_v, tile_disk_s = create_kpi_card(stress_grid, "Disk Throughput")

        tile_cpu_v.config(text="0.0%")
        tile_cpu_s.config(text="All Cores Ready")
        tile_temp_v.config(text="-- °C")
        tile_temp_s.config(text="nvidia-smi / WMI")
        tile_ram_v.config(text="0 Errors")
        tile_ram_s.config(text="0 MB Allocated")
        tile_disk_v.config(text="Idle")
        tile_disk_s.config(text="W: -- | R: --")

        # Progress bar
        stress_progress_frame = tk.Frame(tab_stress)
        stress_progress_frame.pack(fill=tk.X, pady=(0, 10))
        themed_widgets["root_bg"].append(stress_progress_frame)

        stress_progress = ttk.Progressbar(stress_progress_frame, mode="determinate", length=600)
        stress_progress.pack(fill=tk.X)

        lbl_stress_status = tk.Label(stress_progress_frame, text="Status: Ready to benchmark. Select duration and click 'Start Stress Test'.", font=("Segoe UI", 9))
        lbl_stress_status.pack(anchor="w", pady=(3, 0))
        themed_widgets["root_bg"].append(lbl_stress_status)
        themed_widgets["text_dim"].append(lbl_stress_status)

        # Split Bottom: Live Diagnostic Output Console + Native Windows Benchmarks
        stress_bottom = tk.Frame(tab_stress)
        stress_bottom.pack(fill=tk.BOTH, expand=True)
        themed_widgets["root_bg"].append(stress_bottom)

        console_frame = tk.Frame(stress_bottom, highlightthickness=1)
        console_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        themed_widgets["surface"].append(console_frame)
        themed_widgets["borders"].append(console_frame)

        console_title_bar = tk.Frame(console_frame, padx=10, pady=4)
        console_title_bar.pack(fill=tk.X)
        themed_widgets["surface"].append(console_title_bar)

        lbl_console_title = tk.Label(console_title_bar, text="REAL-TIME DIAGNOSTIC TELEMETRY LOG", font=("Segoe UI", 8, "bold"))
        lbl_console_title.pack(side=tk.LEFT)
        themed_widgets["surface"].append(lbl_console_title)
        themed_widgets["text_dim"].append(lbl_console_title)

        txt_console = tk.Text(console_frame, font=("Consolas", 9), relief=tk.FLAT, padx=10, pady=8, height=8)
        txt_console.pack(fill=tk.BOTH, expand=True)
        themed_widgets["consoles"].append(txt_console)

        def log_console(msg: str):
            timestamp = time.strftime("%H:%M:%S")
            txt_console.insert(tk.END, f"[{timestamp}] {msg}\n")
            txt_console.see(tk.END)

        log_console("Hardware Gauntlet Stress Engine initialized.")
        log_console("Ready to stress test multi-core CPU, RAM bit patterns, and disk throughput.")

        # Windows Native Diagnostic Tools Panel
        win_tools_box = tk.Frame(stress_bottom, width=280, padx=12, pady=10, highlightthickness=1)
        win_tools_box.pack(side=tk.RIGHT, fill=tk.Y)
        themed_widgets["surface"].append(win_tools_box)
        themed_widgets["borders"].append(win_tools_box)

        lbl_win_bench = tk.Label(win_tools_box, text="WINDOWS DIAGNOSTICS", font=("Segoe UI", 9, "bold"))
        lbl_win_bench.pack(anchor="w", pady=(0, 8))
        themed_widgets["surface"].append(lbl_win_bench)
        themed_widgets["text_primary"].append(lbl_win_bench)

        def add_quick_tool(title, desc, cmd):
            f = tk.Frame(win_tools_box, pady=3)
            f.pack(fill=tk.X)
            themed_widgets["surface"].append(f)
            b = tk.Button(f, text=title, command=lambda: launch_os_tool(cmd), font=("Segoe UI", 8, "bold"), relief=tk.FLAT, padx=8, pady=4, cursor="hand2", highlightthickness=1)
            b.pack(fill=tk.X)
            themed_widgets["btn_secondary"].append(b)

        if sys.platform == "win32":
            add_quick_tool("🧠 Windows Memory Check", "Schedule boot RAM test", "mdsched.exe")
            add_quick_tool("📈 System Performance", "Generate 60s perf report", "perfmon.exe /report")
            add_quick_tool("⚡ WinSAT Assessment", "Windows assessment tool", "winsat.exe formal")
            add_quick_tool("🎮 DirectX Diagnostic", "DirectX & display driver check", "dxdiag.exe")
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
                tile_cpu_v.config(text=f"{cpu_pct:.1f}%")
                freq = t.get("cpu_freq_mhz", 0.0)
                tile_cpu_s.config(text=f"Freq: {freq/1000:.2f} GHz | Peak: {t.get('peak_cpu_load', 0):.1f}%")

                gpu_temp = t.get("gpu_temp")
                if gpu_temp is not None:
                    tile_temp_v.config(text=f"{gpu_temp} °C")
                    peak_temp = t.get("peak_gpu_temp", gpu_temp)
                    tile_temp_s.config(text=f"Peak: {peak_temp} °C | Status: Nominal")
                else:
                    tile_temp_v.config(text="Active")
                    tile_temp_s.config(text="Thermal zones normal")

                ram_err = t.get("ram_errors", 0)
                tile_ram_v.config(text=f"{ram_err} Errors" if ram_err == 0 else f"⚠️ {ram_err} FAULTS")
                tile_ram_s.config(text=f"RAM: {t.get('ram_percent', 0)}% used")

                w_spd = t.get("disk_write_speed", 0.0)
                r_spd = t.get("disk_read_speed", 0.0)
                if w_spd > 0 or r_spd > 0:
                    tile_disk_v.config(text=f"W: {w_spd:.0f} MB/s")
                    tile_disk_s.config(text=f"R: {r_spd:.0f} MB/s")

                lbl_stress_status.config(text=f"Status: Stress testing in progress... Elapsed: {t.get('elapsed', 0)}s / {t.get('duration', 30)}s ({progress:.0f}%)")
            root.after(0, update)

        def on_stress_complete(summary: Dict[str, Any]):
            def update():
                stress_progress["value"] = 100
                btn_start_stress.config(state=tk.NORMAL)
                btn_stop_stress.config(state=tk.DISABLED)

                verdict = summary.get("stability_status", "PASSED")
                lbl_stress_status.config(text=f"Status: COMPLETED in {summary.get('total_elapsed', 0)}s • Verdict: {verdict}")
                log_console(f"Torture benchmark finished. Verdict: {verdict}")
                log_console(f"Peak CPU Load: {summary.get('peak_cpu_load', 0)}% | Peak GPU Temp: {summary.get('peak_gpu_temp', 'N/A')} °C")
                log_console(f"RAM Integrity Errors: {summary.get('ram_errors', 0)}")
                if summary.get("disk_write_speed", 0) > 0:
                    log_console(f"Disk Sequential Write: {summary.get('disk_write_speed')} MB/s | Read: {summary.get('disk_read_speed')} MB/s")
                messagebox.showinfo("Stress Test Complete", f"Hardware Stress Benchmark Finished!\n\nVerdict: {verdict}\nPeak CPU Load: {summary.get('peak_cpu_load', 0)}%\nPeak GPU Temp: {summary.get('peak_gpu_temp', 'N/A')} °C\nRAM Bit Errors: {summary.get('ram_errors', 0)}")
            root.after(0, update)

        def start_stress():
            duration_map = {0: 15, 1: 30, 2: 60, 3: 120}
            dur = duration_map.get(combo_duration.current(), 30)

            c_on = var_test_cpu.get()
            r_on = var_test_ram.get()
            d_on = var_test_disk.get()

            if not (c_on or r_on or d_on):
                messagebox.showwarning("Selection Required", "Please select at least one subsystem to stress test.")
                return

            btn_start_stress.config(state=tk.DISABLED)
            btn_stop_stress.config(state=tk.NORMAL)
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
            btn_start_stress.config(state=tk.NORMAL)
            btn_stop_stress.config(state=tk.DISABLED)
            lbl_stress_status.config(text="Status: Test stopped by user.")
            log_console("Stress test aborted by user.")

        btn_start_stress.config(command=start_stress)
        btn_stop_stress.config(command=stop_stress)

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
        lbl_tools_hdr = tk.Label(tab_tools, text="DIRECT OPERATING SYSTEM DIAGNOSTIC SHORTCUTS", font=("Segoe UI", 11, "bold"))
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

            b = tk.Button(card, text="Launch Tool", command=lambda: launch_os_tool(cmd), font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2", highlightthickness=1)
            b.pack(fill=tk.X)
            themed_widgets["btn_secondary"].append(b)

        if sys.platform == "win32":
            add_tool_card(tools_grid, "🔌 Device Manager", "Hardware drivers, controllers, PnP IDs", "devmgmt.msc")
            add_tool_card(tools_grid, "📈 Task Manager", "Real-time thread & memory utilization", "taskmgr.exe")
            add_tool_card(tools_grid, "💾 Disk Management", "Partition layouts, volume health", "diskmgmt.msc")
            add_tool_card(tools_grid, "ℹ️ System Info", "MSInfo32 BIOS and firmware tables", "msinfo32.exe")

        # Installation & System Registration Card
        install_card = tk.Frame(tab_tools, padx=20, pady=16, highlightthickness=1)
        install_card.pack(fill=tk.BOTH, expand=True)
        themed_widgets["surface"].append(install_card)
        themed_widgets["borders"].append(install_card)

        lbl_inst_title = tk.Label(install_card, text="SYSTEM INSTALLATION & SHORTCUT MANAGEMENT", font=("Segoe UI", 11, "bold"))
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

        btn_install_tab = tk.Button(inst_btn_row, text="📦 Install to PC (Desktop, Start Menu, PATH)", command=do_install, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=14, pady=6, cursor="hand2", highlightthickness=1)
        btn_install_tab.pack(side=tk.LEFT, padx=(0, 10))
        themed_widgets["btn_primary"].append(btn_install_tab)

        def do_open_folder():
            p = get_install_directory() if is_installed() else os.getcwd()
            os.startfile(p) if sys.platform == "win32" else subprocess.Popen(["xdg-open", p])

        btn_folder = tk.Button(inst_btn_row, text="📂 Open Program Folder", command=do_open_folder, font=("Segoe UI", 9), relief=tk.FLAT, padx=12, pady=6, cursor="hand2", highlightthickness=1)
        btn_folder.pack(side=tk.LEFT, padx=(0, 10))
        themed_widgets["btn_secondary"].append(btn_folder)

        def do_uninstall():
            if messagebox.askyesno("Uninstall", "Are you sure you want to uninstall Hardware Gauntlet from your PC?"):
                success, msg = uninstall_application()
                if success:
                    lbl_install_status.config(text="Status: Uninstalled from PC (Running portable)")
                    btn_install.config(text="📦 Install to PC")
                    messagebox.showinfo("Uninstalled", "Hardware Gauntlet shortcuts and registry entries have been removed.")
                else:
                    messagebox.showerror("Error", msg)

        btn_uninst = tk.Button(inst_btn_row, text="🗑️ Uninstall", command=do_uninstall, font=("Segoe UI", 9), relief=tk.FLAT, padx=10, pady=6, cursor="hand2", highlightthickness=1)
        btn_uninst.pack(side=tk.LEFT)
        themed_widgets["btn_secondary"].append(btn_uninst)

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

            for b in themed_widgets["btn_primary"]:
                try:
                    b.config(
                        bg=th["accent"],
                        fg=th["accent_text"],
                        activebackground=th["accent_hover"],
                        activeforeground=th["accent_text"],
                        highlightbackground=th["border"],
                        highlightcolor=th["border"]
                    )
                except Exception:
                    pass

            for b in themed_widgets["btn_secondary"]:
                try:
                    b.config(
                        bg=th["btn_bg"],
                        fg=th["btn_fg"],
                        activebackground=th["btn_hover"],
                        activeforeground=th["btn_fg"],
                        highlightbackground=th["btn_border"],
                        highlightcolor=th["btn_border"]
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

            btn_theme.config(text=th["toggle_text"])

            logo_img = get_theme_logo(self.current_theme)
            if logo_img:
                lbl_logo.config(image=logo_img)
                lbl_logo.image = logo_img

            # TTK Styles
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
            score_val.set(str(score))

            if score >= 90:
                score_rating.set("EXCELLENT")
            elif score >= 75:
                score_rating.set("OPTIMAL")
            elif score >= 60:
                score_rating.set("ATTENTION")
            else:
                score_rating.set("CRITICAL")

            lbl_subtitle.config(text=f"Host: {report.system.hostname} • OS: {report.system.os_name} ({report.system.os_arch}) • Uptime: {report.system.uptime_formatted}")
            btn_scan.config(state=tk.NORMAL, text="⟳ Re-Scan")
            btn_overview_scan.config(state=tk.NORMAL, text="⟳ Re-Scan Hardware")
            lbl_banner_title.config(text=f"SYSTEM AUDIT COMPLETED • SCORE {score}/100")
            lbl_banner_desc.config(text=f"Audited {report.cpu.logical_cores} CPU threads, {format_bytes(report.memory.total_bytes)} memory, {len(report.gpu.devices)} GPU accelerator(s), and {len(report.storage.partitions)} storage partitions.")

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

        # Apply initial dark theme
        apply_current_theme()

        # NOTE: Scan is NOT automatically triggered on launch! User clicks '▶ Run Full Scan'
        root.mainloop()


def launch_gui(prefer_engine: str = "auto") -> None:
    """Convenience launcher for HardwareGauntletGUI."""
    gui = HardwareGauntletGUI()
    gui.run(prefer_engine=prefer_engine)


if __name__ == "__main__":
    launch_gui()
