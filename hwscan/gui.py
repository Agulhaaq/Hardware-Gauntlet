"""Native Desktop GUI Application for Hardware Gauntlet with Clean Modern UI & Dark/Light Themes."""

import os
import sys
import json
import subprocess
import webbrowser
import threading
from typing import Optional, Dict, Any

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.core.utils import format_bytes, format_hz


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


class HardwareGauntletGUI:
    """Orchestrates launching the modern clean desktop application with dual dark/light themes."""

    def __init__(self):
        self.engine = HardwareScannerEngine()
        self.html_reporter = HTMLReporter()
        self.json_reporter = JSONReporter()
        self.current_report = None
        self.current_theme = "dark"

    def run(self, prefer_engine: str = "auto") -> None:
        """Launch the native desktop application window."""
        self._run_tkinter()

    def _run_tkinter(self) -> None:
        """Render native Tkinter GUI with instant launch, clean modern layout and theme toggling."""
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog

        root = tk.Tk()
        root.title("Hardware Gauntlet - Hardware Diagnostic Suite")
        root.geometry("1140x780")
        root.minsize(920, 640)

        # Set window icon
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "app.ico")
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
            "treeviews": [],
        }

        style = ttk.Style()
        style.theme_use("clam")

        # -------------------------------------------------------------
        # Header Toolbar
        # -------------------------------------------------------------
        header = tk.Frame(root, padx=24, pady=16, highlightthickness=1)
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

        lbl_subtitle = tk.Label(title_text_box, text="Scanning local hardware telemetry in background...", font=("Segoe UI", 9))
        lbl_subtitle.pack(anchor="w", pady=(2, 0))
        themed_widgets["surface"].append(lbl_subtitle)
        themed_widgets["text_dim"].append(lbl_subtitle)

        # Action Buttons Right
        btn_frame = tk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        themed_widgets["surface"].append(btn_frame)

        # Health Score Pill Card
        score_val = tk.StringVar(value="...")
        score_rating = tk.StringVar(value="SCANNING")
        
        score_card = tk.Frame(btn_frame, padx=14, pady=6, highlightthickness=1)
        score_card.pack(side=tk.LEFT, padx=(0, 14))
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
        def do_refresh():
            btn_refresh.config(state=tk.DISABLED, text="⏳ Scanning...")
            lbl_subtitle.config(text="Refreshing hardware audit components...")
            threading.Thread(target=run_background_scan, daemon=True).start()

        def do_export_html():
            if not self.current_report:
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

        # Toolbar Buttons
        btn_theme = tk.Button(btn_frame, command=toggle_theme, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, pady=6, cursor="hand2", highlightthickness=1)
        btn_theme.pack(side=tk.LEFT, padx=4)
        themed_widgets["btn_secondary"].append(btn_theme)

        btn_refresh = tk.Button(btn_frame, text="⟳ Refresh", command=do_refresh, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, pady=6, cursor="hand2", highlightthickness=1)
        btn_refresh.pack(side=tk.LEFT, padx=4)
        themed_widgets["btn_secondary"].append(btn_refresh)

        btn_html = tk.Button(btn_frame, text="📄 Export HTML", command=do_export_html, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=14, pady=6, cursor="hand2", highlightthickness=1)
        btn_html.pack(side=tk.LEFT, padx=4)
        themed_widgets["btn_primary"].append(btn_html)

        btn_json = tk.Button(btn_frame, text="💾 JSON", command=do_export_json, font=("Segoe UI", 9), relief=tk.FLAT, padx=10, pady=6, cursor="hand2", highlightthickness=1)
        btn_json.pack(side=tk.LEFT, padx=4)
        themed_widgets["btn_secondary"].append(btn_json)

        # -------------------------------------------------------------
        # Main Tab Navigation
        # -------------------------------------------------------------
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=18, pady=(12, 18))

        def create_tab(title):
            tab = tk.Frame(notebook, padx=16, pady=16)
            notebook.add(tab, text=title)
            themed_widgets["root_bg"].append(tab)
            return tab

        tab_overview = create_tab("📊 Overview")
        tab_cpu = create_tab("🧠 CPU & Board")
        tab_mem = create_tab("💾 Memory")
        tab_gpu = create_tab("🎮 Graphics")
        tab_storage = create_tab("💽 Storage")
        tab_security = create_tab("🔒 Security")
        tab_tools = create_tab("🛠️ Diagnostics")

        # -------------------------------------------------------------
        # Tab 1: Overview & Modern KPI Tiles
        # -------------------------------------------------------------
        kpi_grid = tk.Frame(tab_overview)
        kpi_grid.pack(fill=tk.X, pady=(0, 16))
        themed_widgets["root_bg"].append(kpi_grid)

        def create_kpi_card(parent, title):
            card = tk.Frame(parent, padx=18, pady=14, highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
            themed_widgets["surface"].append(card)
            themed_widgets["borders"].append(card)

            lbl_t = tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"))
            lbl_t.pack(anchor="w")
            themed_widgets["surface"].append(lbl_t)
            themed_widgets["text_dim"].append(lbl_t)

            lbl_v = tk.Label(card, text="Detecting...", font=("Segoe UI", 12, "bold"))
            lbl_v.pack(anchor="w", pady=(3, 2))
            themed_widgets["surface"].append(lbl_v)
            themed_widgets["text_primary"].append(lbl_v)

            lbl_s = tk.Label(card, text="System telemetry", font=("Segoe UI", 8))
            lbl_s.pack(anchor="w")
            themed_widgets["surface"].append(lbl_s)
            themed_widgets["text_dim"].append(lbl_s)
            return lbl_v, lbl_s

        kpi_cpu_v, kpi_cpu_s = create_kpi_card(kpi_grid, "Processor (CPU)")
        kpi_mem_v, kpi_mem_s = create_kpi_card(kpi_grid, "Memory (RAM)")
        kpi_gpu_v, kpi_gpu_s = create_kpi_card(kpi_grid, "Graphics (GPU)")
        kpi_sec_v, kpi_sec_s = create_kpi_card(kpi_grid, "Security & Boot")

        # Findings Header
        lbl_findings_hdr = tk.Label(tab_overview, text="HARDWARE DIAGNOSTIC FINDINGS & ALERTS", font=("Segoe UI", 10, "bold"))
        lbl_findings_hdr.pack(anchor="w", pady=(8, 6))
        themed_widgets["root_bg"].append(lbl_findings_hdr)
        themed_widgets["text_primary"].append(lbl_findings_hdr)

        tree_warn = ttk.Treeview(tab_overview, columns=("level", "category", "details"), show="headings", height=9)
        tree_warn.heading("level", text="Severity")
        tree_warn.heading("category", text="Category")
        tree_warn.heading("details", text="Observation & Recommendation")
        tree_warn.column("level", width=110, anchor="center")
        tree_warn.column("category", width=140)
        tree_warn.column("details", width=720)
        tree_warn.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_warn)

        # -------------------------------------------------------------
        # Tab 2: CPU & Motherboard
        # -------------------------------------------------------------
        tree_cpu = ttk.Treeview(tab_cpu, columns=("prop", "val"), show="headings")
        tree_cpu.heading("prop", text="Hardware Specification")
        tree_cpu.heading("val", text="Observed Value")
        tree_cpu.column("prop", width=280)
        tree_cpu.column("val", width=740)
        tree_cpu.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_cpu)

        # -------------------------------------------------------------
        # Tab 3: RAM & DIMMs
        # -------------------------------------------------------------
        tree_mem = ttk.Treeview(tab_mem, columns=("slot", "cap", "type", "speed", "mfg", "part"), show="headings")
        tree_mem.heading("slot", text="DIMM Slot / Bank")
        tree_mem.heading("cap", text="Module Capacity")
        tree_mem.heading("type", text="Memory Gen")
        tree_mem.heading("speed", text="Clock Speed")
        tree_mem.heading("mfg", text="Manufacturer")
        tree_mem.heading("part", text="Module Part Number")
        for col in ("slot", "cap", "type", "speed", "mfg", "part"):
            tree_mem.column(col, width=155)
        tree_mem.pack(fill=tk.BOTH, expand=True)
        themed_widgets["treeviews"].append(tree_mem)

        # -------------------------------------------------------------
        # Tab 4: GPU & Displays
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
        # Tab 5: Storage & Partitions
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
        # Tab 6: Security & Network
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
        # Tab 7: System Tools & Diagnostics
        # -------------------------------------------------------------
        lbl_tools_hdr = tk.Label(tab_tools, text="DIRECT OPERATING SYSTEM DIAGNOSTIC SHORTCUTS", font=("Segoe UI", 11, "bold"))
        lbl_tools_hdr.pack(anchor="w", pady=(0, 16))
        themed_widgets["root_bg"].append(lbl_tools_hdr)
        themed_widgets["text_primary"].append(lbl_tools_hdr)

        tools_grid = tk.Frame(tab_tools)
        tools_grid.pack(fill=tk.X, pady=(0, 20))
        themed_widgets["root_bg"].append(tools_grid)

        def add_tool_card(parent, title, desc, cmd):
            card = tk.Frame(parent, padx=16, pady=16, highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
            themed_widgets["surface"].append(card)
            themed_widgets["borders"].append(card)

            t = tk.Label(card, text=title, font=("Segoe UI", 11, "bold"))
            t.pack(anchor="w")
            themed_widgets["surface"].append(t)
            themed_widgets["text_primary"].append(t)

            d = tk.Label(card, text=desc, font=("Segoe UI", 8))
            d.pack(anchor="w", pady=(3, 12))
            themed_widgets["surface"].append(d)
            themed_widgets["text_dim"].append(d)

            b = tk.Button(card, text="Launch Tool", command=lambda: launch_os_tool(cmd), font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2", highlightthickness=1)
            b.pack(fill=tk.X)
            themed_widgets["btn_secondary"].append(b)

        if sys.platform == "win32":
            add_tool_card(tools_grid, "🔌 Device Manager", "Hardware drivers, controllers, PnP IDs", "devmgmt.msc")
            add_tool_card(tools_grid, "📈 Task Manager", "Real-time thread & memory utilization", "taskmgr.exe")
            add_tool_card(tools_grid, "💾 Disk Management", "Partition layouts, volume health", "diskmgmt.msc")
            add_tool_card(tools_grid, "ℹ️ System Info", "MSInfo32 BIOS and firmware tables", "msinfo32.exe")
        else:
            lbl_linux_tools = tk.Label(tools_grid, text="Platform diagnostic utilities available via your desktop system menu.", font=("Segoe UI", 9))
            lbl_linux_tools.pack(anchor="w")
            themed_widgets["root_bg"].append(lbl_linux_tools)
            themed_widgets["text_dim"].append(lbl_linux_tools)

        # Installation Status Panel
        info_box = tk.Frame(tab_tools, padx=22, pady=18, highlightthickness=1)
        info_box.pack(fill=tk.BOTH, expand=True)
        themed_widgets["surface"].append(info_box)
        themed_widgets["borders"].append(info_box)

        lbl_info_title = tk.Label(info_box, text="HARDWARE GAUNTLET LOCAL SUITE STATUS", font=("Segoe UI", 11, "bold"))
        lbl_info_title.pack(anchor="w")
        themed_widgets["surface"].append(lbl_info_title)
        themed_widgets["text_primary"].append(lbl_info_title)

        info_text = (
            "• Running Mode: Native Offline Client Application (Zero Network / No Localhost Required)\n"
            "• Scanning Architecture: In-Memory Multi-Threaded Telemetry Collector\n"
            "• Export Engine: Standalone Self-Contained HTML and JSON reports saved directly to disk\n"
            "• System Integration: Desktop Shortcut, Start Menu, User PATH, and Windows Settings Uninstaller"
        )
        lbl_info_body = tk.Label(info_box, text=info_text, font=("Segoe UI", 9), justify=tk.LEFT)
        lbl_info_body.pack(anchor="w", pady=(8, 0))
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
            p = os.path.join(base_dir, "assets", cfg["logo_file"])
            if not os.path.exists(p):
                p = os.path.join(base_dir, "assets", cfg["logo_fallback"])
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

            # 1. Root & background frames
            for w in themed_widgets["root_bg"]:
                try:
                    w.config(bg=th["bg"])
                except Exception:
                    pass

            # 2. Surface containers (header, cards, info boxes)
            for w in themed_widgets["surface"]:
                try:
                    w.config(bg=th["surface"])
                except Exception:
                    pass

            # 3. Card widgets
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

            # 4. Borders
            for w in themed_widgets["borders"]:
                try:
                    w.config(highlightbackground=th["border"], highlightcolor=th["border"])
                except Exception:
                    pass

            # 5. Text primary
            for w in themed_widgets["text_primary"]:
                try:
                    w.config(fg=th["text"])
                except Exception:
                    pass

            # 6. Text dim & muted
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

            # 7. Action buttons
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

            btn_theme.config(text=th["toggle_text"])

            # 8. Logo swap
            logo_img = get_theme_logo(self.current_theme)
            if logo_img:
                lbl_logo.config(image=logo_img)
                lbl_logo.image = logo_img

            # 9. TTK Styles for Notebook & Treeviews
            style.configure("TNotebook", background=th["bg"], borderwidth=0)
            style.configure(
                "TNotebook.Tab",
                background=th["tab_bg"],
                foreground=th["tab_fg"],
                padding=[18, 9],
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
                rowheight=30,
                borderwidth=0
            )
            style.configure(
                "Treeview.Heading",
                background=th["tree_head_bg"],
                foreground=th["tree_head_fg"],
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT,
                padding=[8, 8]
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
            btn_refresh.config(state=tk.NORMAL, text="⟳ Refresh")

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

            # Helper for striped rows
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

        # Trigger background telemetry collection
        root.after(100, run_background_scan)
        root.mainloop()


def launch_gui(prefer_engine: str = "auto") -> None:
    """Convenience launcher for HardwareGauntletGUI."""
    gui = HardwareGauntletGUI()
    gui.run(prefer_engine=prefer_engine)
