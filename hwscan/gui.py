"""Native Desktop GUI Application for Hardware Gauntlet.

Supports dual-mode rendering:
1. High-fidelity WebView2 / WebKit / WebKitGTK native desktop window
2. Standalone Tkinter dark-theme GUI (zero extra dependencies, built into Python)
"""

import os
import sys
import json
import webbrowser
import threading
from typing import Optional

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.core.utils import format_bytes, format_hz


class HardwareGauntletGUI:
    """Orchestrates launching the desktop application window."""

    def __init__(self):
        self.engine = HardwareScannerEngine()
        self.html_reporter = HTMLReporter()
        self.json_reporter = JSONReporter()
        self.current_report = None

    def run(self, prefer_engine: str = "auto") -> None:
        """Launch the GUI desktop application window."""
        # Initial scan
        self.current_report = self.engine.run_full_scan()

        if prefer_engine == "tk":
            self._run_tkinter()
            return

        if prefer_engine in ("auto", "webview"):
            try:
                import webview
                self._run_webview(webview)
                return
            except Exception as e:
                # Fallback gracefully to Tkinter
                pass

        self._run_tkinter()

    def _run_webview(self, webview_module) -> None:
        """Render high-fidelity desktop window via pywebview."""
        from hwscan.web.server import PORTAL_HTML

        report = self.current_report
        html = PORTAL_HTML
        html = html.replace("{{HOSTNAME}}", report.system.hostname)
        html = html.replace("{{OS_NAME}}", f"{report.system.os_name} ({report.system.os_arch})")
        html = html.replace("{{CPU_MODEL}}", report.cpu.model)
        html = html.replace("{{RAM_INFO}}", f"{report.memory.percent}% used of {format_bytes(report.memory.total_bytes)}")
        gpu_str = report.gpu.devices[0].name if report.gpu.devices else "Integrated Graphics"
        html = html.replace("{{GPU_INFO}}", gpu_str)
        html = html.replace("{{HEALTH_SCORE}}", str(report.health_score))
        sec_str = "Secure Boot OK" if report.security.secure_boot else "Standard"
        html = html.replace("{{SECURITY_INFO}}", sec_str)

        # Inject desktop bridge
        class WindowAPI:
            def __init__(self, parent):
                self.parent = parent

            def refresh(self):
                self.parent.current_report = self.parent.engine.run_full_scan()
                return self.parent.current_report.to_dict()

            def export_html(self):
                out_path = os.path.join(os.path.expanduser("~"), "Desktop", f"hardware-report-{self.parent.current_report.system.hostname}.html")
                self.parent.html_reporter.write_file(self.parent.current_report, out_path)
                return out_path

        api = WindowAPI(self)
        window = webview_module.create_window(
            title="Hardware Gauntlet - Universal Hardware Diagnostic Suite",
            html=html,
            js_api=api,
            width=1180,
            height=820,
            min_size=(900, 600),
            background_color="#0b0f19"
        )
        webview_module.start()

    def _run_tkinter(self) -> None:
        """Render native Tkinter dark-theme GUI."""
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog

        root = tk.Tk()
        root.title("Hardware Gauntlet - Universal Hardware Diagnostic Suite")
        root.geometry("1100x750")
        root.minsize(850, 600)

        # Apply dark theme styling
        BG_DARK = "#0b0f19"
        SURFACE = "#111827"
        SURFACE_CARD = "#1e293b"
        TEXT_LIGHT = "#f8fafc"
        TEXT_DIM = "#94a3b8"
        CYAN = "#38bdf8"
        GREEN = "#10b981"
        BORDER = "#334155"

        root.configure(bg=BG_DARK)

        style = ttk.Style()
        style.theme_use("clam")

        # Custom ttk styles
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=SURFACE, foreground=TEXT_DIM, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", CYAN)], foreground=[("selected", "#000000")])
        style.configure("Treeview", background=SURFACE_CARD, foreground=TEXT_LIGHT, fieldbackground=SURFACE_CARD, font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", background=SURFACE, foreground=CYAN, font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#2563eb")])

        # Header Frame
        header = tk.Frame(root, bg=SURFACE, padx=24, pady=16, highlightthickness=1, highlightbackground=BORDER)
        header.pack(fill=tk.X, side=tk.TOP)

        title_frame = tk.Frame(header, bg=SURFACE)
        title_frame.pack(side=tk.LEFT)

        tk.Label(title_frame, text="⚡ HARDWARE GAUNTLET", font=("Segoe UI", 16, "bold"), fg=CYAN, bg=SURFACE).pack(anchor="w")
        sub_text = f"Host: {self.current_report.system.hostname} • OS: {self.current_report.system.os_name} ({self.current_report.system.os_arch})"
        lbl_subtitle = tk.Label(title_frame, text=sub_text, font=("Segoe UI", 10), fg=TEXT_DIM, bg=SURFACE)
        lbl_subtitle.pack(anchor="w")

        # Action Buttons Frame
        btn_frame = tk.Frame(header, bg=SURFACE)
        btn_frame.pack(side=tk.RIGHT)

        def do_refresh():
            self.current_report = self.engine.run_full_scan()
            refresh_views()
            messagebox.showinfo("Hardware Scan", f"Hardware scan updated in {self.current_report.scan_duration_seconds}s!")

        def do_export_html():
            f = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Files", "*.html")],
                initialfile=f"hardware-report-{self.current_report.system.hostname}.html"
            )
            if f:
                self.html_reporter.write_file(self.current_report, f)
                if messagebox.askyesno("Report Saved", f"HTML Report saved successfully!\nOpen it in your browser?"):
                    webbrowser.open(f)

        def do_export_json():
            f = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                initialfile=f"hardware-report-{self.current_report.system.hostname}.json"
            )
            if f:
                self.json_reporter.write_file(self.current_report, f)
                messagebox.showinfo("JSON Saved", f"JSON report saved to {f}")

        def do_launch_web():
            from hwscan.web.server import start_server
            threading.Thread(target=start_server, kwargs={"port": 8080}, daemon=True).start()
            webbrowser.open("http://localhost:8080")

        # Score Box
        score_val = tk.StringVar(value=str(self.current_report.health_score))
        score_frame = tk.Frame(btn_frame, bg=SURFACE_CARD, padx=12, pady=6, relief=tk.RIDGE, bd=1)
        score_frame.pack(side=tk.LEFT, padx=12)
        tk.Label(score_frame, textvariable=score_val, font=("Segoe UI", 16, "bold"), fg=GREEN, bg=SURFACE_CARD).pack()
        tk.Label(score_frame, text="HEALTH SCORE", font=("Segoe UI", 8), fg=TEXT_DIM, bg=SURFACE_CARD).pack()

        tk.Button(btn_frame, text="🔄 Refresh Scan", command=do_refresh, font=("Segoe UI", 9, "bold"), bg="#1e293b", fg=TEXT_LIGHT, activebackground="#334155", activeforeground=TEXT_LIGHT, relief=tk.FLAT, padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="📄 Export HTML", command=do_export_html, font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff", relief=tk.FLAT, padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="💾 Export JSON", command=do_export_json, font=("Segoe UI", 9), bg="#1e293b", fg=TEXT_LIGHT, relief=tk.FLAT, padx=10, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="🌐 Web Portal", command=do_launch_web, font=("Segoe UI", 9), bg="#1e293b", fg=CYAN, relief=tk.FLAT, padx=10, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Main Notebook Tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Tab 1: Overview & KPI Cards
        tab_overview = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_overview, text="📊 System Overview")

        # Tab 2: Processor & Motherboard
        tab_cpu = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_cpu, text="🧠 CPU & Motherboard")

        # Tab 3: Memory (RAM)
        tab_mem = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_mem, text="💾 RAM & DIMM Slots")

        # Tab 4: GPU & Displays
        tab_gpu = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_gpu, text="🎮 Graphics & Displays")

        # Tab 5: Storage
        tab_storage = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_storage, text="💽 Drives & Partitions")

        # Tab 6: Multi-OS Downloads
        tab_downloads = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_downloads, text="📥 Downloads Per OS")

        # Overview Content
        kpi_grid = tk.Frame(tab_overview, bg=BG_DARK)
        kpi_grid.pack(fill=tk.X, pady=(0, 16))

        def create_kpi_card(parent, title, val, sub):
            card = tk.Frame(parent, bg=SURFACE, padx=16, pady=12, highlightthickness=1, highlightbackground=BORDER)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
            tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"), fg=TEXT_DIM, bg=SURFACE).pack(anchor="w")
            lbl_v = tk.Label(card, text=val, font=("Segoe UI", 12, "bold"), fg=TEXT_LIGHT, bg=SURFACE)
            lbl_v.pack(anchor="w", pady=2)
            lbl_s = tk.Label(card, text=sub, font=("Segoe UI", 8), fg=TEXT_DIM, bg=SURFACE)
            lbl_s.pack(anchor="w")
            return lbl_v, lbl_s

        kpi_cpu_v, kpi_cpu_s = create_kpi_card(kpi_grid, "Processor (CPU)", self.current_report.cpu.model[:24], f"{self.current_report.cpu.physical_cores} Cores / {self.current_report.cpu.logical_cores} Threads")
        kpi_mem_v, kpi_mem_s = create_kpi_card(kpi_grid, "Memory (RAM)", format_bytes(self.current_report.memory.total_bytes), f"{self.current_report.memory.percent}% in use")
        gpu_name = self.current_report.gpu.devices[0].name[:22] if self.current_report.gpu.devices else "Integrated GPU"
        kpi_gpu_v, kpi_gpu_s = create_kpi_card(kpi_grid, "Graphics (GPU)", gpu_name, self.current_report.gpu.devices[0].vram_formatted if self.current_report.gpu.devices else "Shared VRAM")
        sec_str = "Secure Boot OK" if self.current_report.security.secure_boot else "Secure Boot OFF"
        kpi_sec_v, kpi_sec_s = create_kpi_card(kpi_grid, "Security & Boot", sec_str, f"TPM: {'Active' if self.current_report.security.tpm_present else 'None'}")

        # Overview Diagnostics Box
        tk.Label(tab_overview, text="🔍 DIAGNOSTICS & HEALTH FINDINGS", font=("Segoe UI", 11, "bold"), fg=CYAN, bg=BG_DARK).pack(anchor="w", pady=(8, 4))
        tree_warn = ttk.Treeview(tab_overview, columns=("level", "category", "details"), show="headings", height=8)
        tree_warn.heading("level", text="Level")
        tree_warn.heading("category", text="Category")
        tree_warn.heading("details", text="Finding & Recommendation")
        tree_warn.column("level", width=120)
        tree_warn.column("category", width=140)
        tree_warn.column("details", width=700)
        tree_warn.pack(fill=tk.BOTH, expand=True)

        # Tab 2: CPU Tree
        tree_cpu = ttk.Treeview(tab_cpu, columns=("prop", "val"), show="headings")
        tree_cpu.heading("prop", text="Hardware Property")
        tree_cpu.heading("val", text="Specification")
        tree_cpu.column("prop", width=260)
        tree_cpu.column("val", width=700)
        tree_cpu.pack(fill=tk.BOTH, expand=True)

        # Tab 3: RAM Tree
        tree_mem = ttk.Treeview(tab_mem, columns=("slot", "cap", "type", "speed", "mfg", "part"), show="headings")
        tree_mem.heading("slot", text="Slot / Bank")
        tree_mem.heading("cap", text="Capacity")
        tree_mem.heading("type", text="Type")
        tree_mem.heading("speed", text="Clock Speed")
        tree_mem.heading("mfg", text="Manufacturer")
        tree_mem.heading("part", text="Part Number")
        for col in ("slot", "cap", "type", "speed", "mfg", "part"):
            tree_mem.column(col, width=150)
        tree_mem.pack(fill=tk.BOTH, expand=True)

        # Tab 4: GPU Tree
        tree_gpu = ttk.Treeview(tab_gpu, columns=("name", "vendor", "vram", "driver", "res"), show="headings")
        tree_gpu.heading("name", text="Graphics Card Name")
        tree_gpu.heading("vendor", text="Vendor")
        tree_gpu.heading("vram", text="Dedicated VRAM")
        tree_gpu.heading("driver", text="Driver Version")
        tree_gpu.heading("res", text="Display Mode")
        tree_gpu.pack(fill=tk.BOTH, expand=True)

        # Tab 5: Storage Tree
        tree_storage = ttk.Treeview(tab_storage, columns=("mount", "fs", "total", "used", "free", "percent"), show="headings")
        tree_storage.heading("mount", text="Drive / Mount")
        tree_storage.heading("fs", text="Filesystem")
        tree_storage.heading("total", text="Total Capacity")
        tree_storage.heading("used", text="Used Space")
        tree_storage.heading("free", text="Free Space")
        tree_storage.heading("percent", text="Utilization")
        tree_storage.pack(fill=tk.BOTH, expand=True)

        # Tab 6: Downloads Per OS Card Grid
        tk.Label(tab_downloads, text="⚡ DOWNLOAD & RUN HARDWARE GAUNTLET FOR ALL PLATFORMS", font=("Segoe UI", 12, "bold"), fg=CYAN, bg=BG_DARK).pack(anchor="w", pady=(0, 16))

        dl_cards_frame = tk.Frame(tab_downloads, bg=BG_DARK)
        dl_cards_frame.pack(fill=tk.BOTH, expand=True)

        def create_os_download_card(parent, icon, title, desc, dl_url, run_cmd):
            card = tk.Frame(parent, bg=SURFACE, padx=20, pady=20, highlightthickness=1, highlightbackground=BORDER)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

            tk.Label(card, text=f"{icon} {title}", font=("Segoe UI", 14, "bold"), fg=TEXT_LIGHT, bg=SURFACE).pack(anchor="w")
            tk.Label(card, text=desc, font=("Segoe UI", 9), fg=TEXT_DIM, bg=SURFACE).pack(anchor="w", pady=(2, 12))

            def open_download():
                webbrowser.open(dl_url)

            def copy_cmd():
                root.clipboard_clear()
                root.clipboard_append(run_cmd)
                messagebox.showinfo("Copied", f"Command copied to clipboard:\n\n{run_cmd}")

            tk.Button(card, text="⬇️ Download Binary", command=open_download, font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", padx=12, pady=6, relief=tk.FLAT, cursor="hand2").pack(fill=tk.X, pady=(0, 8))
            tk.Button(card, text="📋 Copy 1-Line Run Command", command=copy_cmd, font=("Segoe UI", 8), bg=SURFACE_CARD, fg=CYAN, padx=8, pady=4, relief=tk.FLAT, cursor="hand2").pack(fill=tk.X)

            cmd_box = tk.Label(card, text=run_cmd, font=("Consolas", 8), fg="#7dd3fc", bg="#090d16", wraplength=260, justify=tk.LEFT, padx=6, pady=6)
            cmd_box.pack(fill=tk.X, pady=(8, 0))

        create_os_download_card(
            dl_cards_frame,
            "🪟", "Windows (x64 / ARM)",
            "Single standalone .exe binary with WMI & CIM hardware telemetry.",
            "https://github.com/Agulhaaq/Hardware-Gauntlet/releases/latest/download/hwscan-windows-x64.exe",
            "irm https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.ps1 | iex"
        )

        create_os_download_card(
            dl_cards_frame,
            "🍎", "macOS (Apple / Intel)",
            "Universal binary for Apple Silicon (M1-M4) & Intel Macs with IOKit.",
            "https://github.com/Agulhaaq/Hardware-Gauntlet/releases/latest/download/hwscan-macos-universal",
            "curl -fsSL https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.sh | bash"
        )

        create_os_download_card(
            dl_cards_frame,
            "🐧", "Linux (Ubuntu / Fedora)",
            "Linux binary compatible with all distros via /proc & DMI parsing.",
            "https://github.com/Agulhaaq/Hardware-Gauntlet/releases/latest/download/hwscan-linux-x64",
            "curl -fsSL https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.sh | bash"
        )

        # Refresh all views
        def refresh_views():
            r = self.current_report
            score_val.set(str(r.health_score))
            lbl_subtitle.config(text=f"Host: {r.system.hostname} • OS: {r.system.os_name} ({r.system.os_arch}) • Uptime: {r.system.uptime_formatted}")

            kpi_cpu_v.config(text=r.cpu.model[:24])
            kpi_cpu_s.config(text=f"{r.cpu.physical_cores} Cores / {r.cpu.logical_cores} Threads @ {format_hz(r.cpu.max_clock_mhz)}")
            kpi_mem_v.config(text=format_bytes(r.memory.total_bytes))
            kpi_mem_s.config(text=f"{r.memory.percent}% used ({format_bytes(r.memory.used_bytes)})")

            # Warnings
            tree_warn.delete(*tree_warn.get_children())
            if r.warnings:
                for w in r.warnings:
                    tree_warn.insert("", tk.END, values=(w.level, w.category, f"{w.title}: {w.description}"))
            else:
                tree_warn.insert("", tk.END, values=("HEALTHY", "System", "All hardware parameters operating normally."))

            # CPU & Motherboard
            tree_cpu.delete(*tree_cpu.get_children())
            cpu_rows = [
                ("Operating System", f"{r.system.os_name} (Build {r.system.os_build})"),
                ("Kernel & Architecture", f"{r.system.kernel} ({r.system.os_arch})"),
                ("Boot Mode", r.system.boot_mode),
                ("Processor Model", r.cpu.model),
                ("Physical / Logical Cores", f"{r.cpu.physical_cores} Physical / {r.cpu.logical_cores} Threads"),
                ("Clock Speeds", f"Max: {format_hz(r.cpu.max_clock_mhz)} (Base: {format_hz(r.cpu.base_clock_mhz)})"),
                ("L2 / L3 Cache", f"L2: {r.cpu.cache_l2} | L3: {r.cpu.cache_l3}"),
                ("CPU Instructions & Features", ", ".join(r.cpu.features)),
                ("Motherboard Vendor", r.motherboard.manufacturer),
                ("Motherboard Model", r.motherboard.product_name),
                ("Motherboard Serial", r.motherboard.serial_number),
                ("BIOS Vendor & Version", f"{r.motherboard.bios_vendor} - v{r.motherboard.bios_version}"),
                ("BIOS Release Date", r.motherboard.bios_release_date),
                ("Chassis Form Factor", r.motherboard.chassis_type),
                ("System Uptime", r.system.uptime_formatted),
            ]
            for p, v in cpu_rows:
                tree_cpu.insert("", tk.END, values=(p, v))

            # RAM
            tree_mem.delete(*tree_mem.get_children())
            if r.memory.modules:
                for m in r.memory.modules:
                    tree_mem.insert("", tk.END, values=(m.bank_label, m.capacity_formatted, m.memory_type, f"{m.speed_mhz} MHz", m.manufacturer, m.part_number))
            else:
                tree_mem.insert("", tk.END, values=("System RAM", format_bytes(r.memory.total_bytes), "RAM", "Standard", "OEM", "N/A"))

            # GPU
            tree_gpu.delete(*tree_gpu.get_children())
            for g in r.gpu.devices:
                tree_gpu.insert("", tk.END, values=(g.name, g.vendor, g.vram_formatted, g.driver_version, g.resolution))

            # Storage
            tree_storage.delete(*tree_storage.get_children())
            for d in r.storage.physical_disks:
                tree_storage.insert("", tk.END, values=(f"[Physical] {d.model}", d.media_type, d.size_formatted, d.interface_type, d.smart_status, "Physical Drive"))
            for p in r.storage.partitions:
                tree_storage.insert("", tk.END, values=(p.mountpoint, p.fstype, p.total_formatted, p.used_formatted, p.free_formatted, f"{p.percent}%"))

        refresh_views()
        root.mainloop()


def launch_gui(prefer_engine: str = "auto") -> None:
    """Convenience launcher for HardwareGauntletGUI."""
    gui = HardwareGauntletGUI()
    gui.run(prefer_engine=prefer_engine)
