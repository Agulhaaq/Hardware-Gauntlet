"""Native Desktop GUI Application for Hardware Gauntlet with Instant Launch."""

import os
import sys
import json
import subprocess
import webbrowser
import threading
from typing import Optional

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.core.utils import format_bytes, format_hz


class HardwareGauntletGUI:
    """Orchestrates launching the desktop application window with instant responsiveness."""

    def __init__(self):
        self.engine = HardwareScannerEngine()
        self.html_reporter = HTMLReporter()
        self.json_reporter = JSONReporter()
        self.current_report = None

    def run(self, prefer_engine: str = "auto") -> None:
        """Launch the native desktop application window."""
        self._run_tkinter()

    def _run_tkinter(self) -> None:
        """Render native Tkinter dark-theme GUI with instant non-blocking launch."""
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog

        root = tk.Tk()
        root.title("Hardware Gauntlet - Hardware Diagnostic Suite")
        root.geometry("1120x760")
        root.minsize(880, 620)

        # Set window icon if available
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "app.ico")
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                root.iconbitmap(ico_path)
            except Exception:
                pass

        # Dark theme color palette
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
        lbl_subtitle = tk.Label(title_frame, text="Scanning local hardware components...", font=("Segoe UI", 10), fg=TEXT_DIM, bg=SURFACE)
        lbl_subtitle.pack(anchor="w")

        # Action Buttons Frame
        btn_frame = tk.Frame(header, bg=SURFACE)
        btn_frame.pack(side=tk.RIGHT)

        score_val = tk.StringVar(value="...")
        score_frame = tk.Frame(btn_frame, bg=SURFACE_CARD, padx=12, pady=6, relief=tk.RIDGE, bd=1)
        score_frame.pack(side=tk.LEFT, padx=12)
        lbl_score_num = tk.Label(score_frame, textvariable=score_val, font=("Segoe UI", 16, "bold"), fg=GREEN, bg=SURFACE_CARD)
        lbl_score_num.pack()
        tk.Label(score_frame, text="HEALTH SCORE", font=("Segoe UI", 8), fg=TEXT_DIM, bg=SURFACE_CARD).pack()

        # Action Callbacks
        def do_refresh():
            btn_refresh.config(state=tk.DISABLED, text="⏳ Scanning...")
            lbl_subtitle.config(text="Scanning local hardware components...")
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
                if messagebox.askyesno("Report Saved", f"Offline HTML report saved successfully to:\n{f}\n\nWould you like to open it?"):
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

        def launch_os_tool(tool_cmd):
            try:
                subprocess.Popen(tool_cmd, shell=True)
            except Exception as err:
                messagebox.showerror("Tool Error", f"Unable to launch {tool_cmd}:\n{err}")

        btn_refresh = tk.Button(btn_frame, text="🔄 Refresh Scan", command=do_refresh, font=("Segoe UI", 9, "bold"), bg="#1e293b", fg=TEXT_LIGHT, activebackground="#334155", activeforeground=TEXT_LIGHT, relief=tk.FLAT, padx=12, pady=6, cursor="hand2")
        btn_refresh.pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="📄 Export HTML Report", command=do_export_html, font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff", relief=tk.FLAT, padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="💾 Export JSON", command=do_export_json, font=("Segoe UI", 9), bg="#1e293b", fg=TEXT_LIGHT, relief=tk.FLAT, padx=10, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)

        # Main Notebook Tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tab_overview = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_overview, text="📊 System Overview")

        tab_cpu = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_cpu, text="🧠 CPU & Motherboard")

        tab_mem = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_mem, text="💾 RAM & DIMM Slots")

        tab_gpu = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_gpu, text="🎮 Graphics & Displays")

        tab_storage = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_storage, text="💽 Drives & Partitions")

        tab_security = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_security, text="🔒 Security & Network")

        tab_tools = tk.Frame(notebook, bg=BG_DARK, padx=16, pady=16)
        notebook.add(tab_tools, text="🛠️ System Diagnostics & Tools")

        # Overview KPI Cards
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

        kpi_cpu_v, kpi_cpu_s = create_kpi_card(kpi_grid, "Processor (CPU)", "Detecting...", "Cores & Threads")
        kpi_mem_v, kpi_mem_s = create_kpi_card(kpi_grid, "Memory (RAM)", "Detecting...", "RAM Usage")
        kpi_gpu_v, kpi_gpu_s = create_kpi_card(kpi_grid, "Graphics (GPU)", "Detecting...", "VRAM & Displays")
        kpi_sec_v, kpi_sec_s = create_kpi_card(kpi_grid, "Security & Boot", "Detecting...", "Secure Boot & TPM")

        # Diagnostics Findings
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

        # Tab 6: Security & Network Tree
        tree_sec = ttk.Treeview(tab_security, columns=("component", "status", "details"), show="headings")
        tree_sec.heading("component", text="Component")
        tree_sec.heading("status", text="Status")
        tree_sec.heading("details", text="Technical Details")
        tree_sec.column("component", width=220)
        tree_sec.column("status", width=180)
        tree_sec.column("details", width=600)
        tree_sec.pack(fill=tk.BOTH, expand=True)

        # Tab 7: System Tools & Diagnostics
        tk.Label(tab_tools, text="🛠️ SYSTEM DIAGNOSTIC SHORTCUTS", font=("Segoe UI", 12, "bold"), fg=CYAN, bg=BG_DARK).pack(anchor="w", pady=(0, 16))
        tools_grid = tk.Frame(tab_tools, bg=BG_DARK)
        tools_grid.pack(fill=tk.X, pady=(0, 24))

        if sys.platform == "win32":
            def add_win_tool(parent, title, desc, cmd):
                card = tk.Frame(parent, bg=SURFACE, padx=16, pady=16, highlightthickness=1, highlightbackground=BORDER)
                card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
                tk.Label(card, text=title, font=("Segoe UI", 11, "bold"), fg=TEXT_LIGHT, bg=SURFACE).pack(anchor="w")
                tk.Label(card, text=desc, font=("Segoe UI", 8), fg=TEXT_DIM, bg=SURFACE).pack(anchor="w", pady=(2, 10))
                tk.Button(card, text="Launch Tool", command=lambda: launch_os_tool(cmd), font=("Segoe UI", 9, "bold"), bg=SURFACE_CARD, fg=CYAN, relief=tk.FLAT, padx=10, pady=4, cursor="hand2").pack(fill=tk.X)

            add_win_tool(tools_grid, "🔌 Device Manager", "Hardware drivers, controllers, PnP IDs", "devmgmt.msc")
            add_win_tool(tools_grid, "📈 Task Manager", "Live CPU threads, RAM & GPU utilization", "taskmgr.exe")
            add_win_tool(tools_grid, "💾 Disk Management", "Partitions, volumes, drive formatting", "diskmgmt.msc")
            add_win_tool(tools_grid, "ℹ️ System Info", "MSInfo32 BIOS & hardware resources", "msinfo32.exe")
        else:
            tk.Label(tools_grid, text="Platform tools available natively in your desktop system menu.", fg=TEXT_DIM, bg=BG_DARK).pack(anchor="w")

        # Integration & Installation Info Box
        info_box = tk.Frame(tab_tools, bg=SURFACE, padx=20, pady=20, highlightthickness=1, highlightbackground=BORDER)
        info_box.pack(fill=tk.BOTH, expand=True)
        tk.Label(info_box, text="⚡ HARDWARE GAUNTLET LOCAL INSTALLATION STATUS", font=("Segoe UI", 11, "bold"), fg=GREEN, bg=SURFACE).pack(anchor="w")
        
        install_text = (
            "• Running Mode: Native Offline Client Application (Zero Network / No Localhost Required)\n"
            "• Scanning Architecture: In-Memory Parallel Threaded Hardware Diagnostic Engine\n"
            "• Export Engine: Self-contained HTML and JSON reports saved directly to your local filesystem\n"
            "• Windows Start Menu & Desktop Integration: Available via setup installer"
        )
        tk.Label(info_box, text=install_text, font=("Segoe UI", 9), fg=TEXT_LIGHT, bg=SURFACE, justify=tk.LEFT).pack(anchor="w", pady=(8, 0))

        # Thread-safe UI update
        def update_ui_with_report(report):
            self.current_report = report
            score_val.set(str(report.health_score))
            lbl_subtitle.config(text=f"Host: {report.system.hostname} • OS: {report.system.os_name} ({report.system.os_arch}) • Uptime: {report.system.uptime_formatted}")
            btn_refresh.config(state=tk.NORMAL, text="🔄 Refresh Scan")

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

            # Warnings
            tree_warn.delete(*tree_warn.get_children())
            if report.warnings:
                for w in report.warnings:
                    tree_warn.insert("", tk.END, values=(w.level, w.category, f"{w.title}: {w.description}"))
            else:
                tree_warn.insert("", tk.END, values=("HEALTHY", "System", "All hardware parameters operating normally."))

            # CPU & Motherboard
            tree_cpu.delete(*tree_cpu.get_children())
            cpu_rows = [
                ("Operating System", f"{report.system.os_name} (Build {report.system.os_build})"),
                ("Kernel & Architecture", f"{report.system.kernel} ({report.system.os_arch})"),
                ("Boot Mode", report.system.boot_mode),
                ("Processor Model", report.cpu.model),
                ("Physical / Logical Cores", f"{report.cpu.physical_cores} Physical / {report.cpu.logical_cores} Threads"),
                ("Clock Speeds", f"Max: {format_hz(report.cpu.max_clock_mhz)} (Base: {format_hz(report.cpu.base_clock_mhz)})"),
                ("L2 / L3 Cache", f"L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}"),
                ("CPU Instructions & Features", ", ".join(report.cpu.features)),
                ("Motherboard Vendor", report.motherboard.manufacturer),
                ("Motherboard Model", report.motherboard.product_name),
                ("Motherboard Serial", report.motherboard.serial_number),
                ("BIOS Vendor & Version", f"{report.motherboard.bios_vendor} - v{report.motherboard.bios_version}"),
                ("BIOS Release Date", report.motherboard.bios_release_date),
                ("Chassis Form Factor", report.motherboard.chassis_type),
                ("System Uptime", report.system.uptime_formatted),
            ]
            for p, v in cpu_rows:
                tree_cpu.insert("", tk.END, values=(p, v))

            # RAM
            tree_mem.delete(*tree_mem.get_children())
            if report.memory.modules:
                for m in report.memory.modules:
                    tree_mem.insert("", tk.END, values=(m.bank_label, m.capacity_formatted, m.memory_type, f"{m.speed_mhz} MHz", m.manufacturer, m.part_number))
            else:
                tree_mem.insert("", tk.END, values=("System RAM", format_bytes(report.memory.total_bytes), "RAM", "Standard", "OEM", "N/A"))

            # GPU
            tree_gpu.delete(*tree_gpu.get_children())
            for g in report.gpu.devices:
                tree_gpu.insert("", tk.END, values=(g.name, g.vendor, g.vram_formatted, g.driver_version, g.resolution))

            # Storage
            tree_storage.delete(*tree_storage.get_children())
            for d in report.storage.physical_disks:
                tree_storage.insert("", tk.END, values=(f"[Physical] {d.model}", d.media_type, d.size_formatted, d.interface_type, d.smart_status, "Physical Drive"))
            for p in report.storage.partitions:
                tree_storage.insert("", tk.END, values=(p.mountpoint, p.fstype, p.total_formatted, p.used_formatted, p.free_formatted, f"{p.percent}%"))

            # Security & Network
            tree_sec.delete(*tree_sec.get_children())
            tree_sec.insert("", tk.END, values=("UEFI Secure Boot", "Enabled" if report.security.secure_boot else "Disabled", "Protects boot integrity against unauthorized bootloaders and rootkits"))
            tree_sec.insert("", tk.END, values=("TPM 2.0 Security", "Active" if report.security.tpm_present else "Not Detected", f"Spec: {report.security.tpm_version or '2.0'} - Hardware cryptography and BitLocker anchor"))
            tree_sec.insert("", tk.END, values=("Virtualization (VT-x/AMD-V)", "Enabled" if report.security.virtualization_enabled else "Disabled", "Hardware virtualization enabled in BIOS/firmware for WSL2, Hyper-V, and VMs"))

            for iface in report.network.interfaces:
                if iface.is_up or iface.ipv4:
                    status = "CONNECTED" if iface.is_up else "DISCONNECTED"
                    ips = ", ".join(iface.ipv4) if iface.ipv4 else "No IPv4"
                    tree_sec.insert("", tk.END, values=(f"Net: {iface.name}", status, f"MAC: {iface.mac_address} | IP: {ips} | Speed: {iface.speed_mbps} Mbps"))

        def run_background_scan():
            rep = self.engine.run_full_scan()
            root.after(0, update_ui_with_report, rep)

        # Trigger background scan immediately after window is drawn
        root.after(100, run_background_scan)
        root.mainloop()


def launch_gui(prefer_engine: str = "auto") -> None:
    """Convenience launcher for HardwareGauntletGUI."""
    gui = HardwareGauntletGUI()
    gui.run(prefer_engine=prefer_engine)
