"""Interactive standalone HTML Diagnostic Report Generator for Hardware Gauntlet.

Styled with duotone monochrome aesthetic, SVG radial thermostat dials, and clean pill components.
"""

import json
import math
from hwscan.core.models import HardwareReport
from hwscan.core.utils import format_bytes, format_hz
from hwscan.assets_data import LOGO_WHITE_B64


class HTMLReporter:
    """Generates a modern, self-contained interactive HTML hardware audit report with radial dials."""

    def _generate_svg_dial(self, score: int, title: str = "HEALTH SCORE") -> str:
        ticks = 42
        start_deg = 135.0
        sweep_deg = 270.0
        active_ticks = int(round((score / 100.0) * ticks))
        lines_svg = []
        cx, cy = 90.0, 90.0
        r_outer = 72.0
        r_inner = 62.0

        for i in range(ticks):
            frac = i / float(ticks - 1)
            deg = start_deg + frac * sweep_deg
            rad = math.radians(deg)
            x1 = cx + r_inner * math.cos(rad)
            y1 = cy + r_inner * math.sin(rad)
            x2 = cx + r_outer * math.cos(rad)
            y2 = cy + r_outer * math.sin(rad)
            color = "var(--dial-active)" if i <= active_ticks else "var(--dial-inactive)"
            width = "3" if i <= active_ticks else "2"
            lines_svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round" />')

        ticks_str = "\n            ".join(lines_svg)
        sub = "OPTIMAL" if score >= 85 else ("ATTENTION" if score >= 70 else "CRITICAL")
        return f"""
        <svg width="180" height="180" viewBox="0 0 180 180" class="dial-svg">
            {ticks_str}
            <text x="90" y="86" text-anchor="middle" class="dial-val">{score}</text>
            <text x="90" y="106" text-anchor="middle" class="dial-sub">{sub}</text>
            <text x="90" y="152" text-anchor="middle" class="dial-title">{title}</text>
        </svg>
        """

    def to_html(self, report: HardwareReport) -> str:
        report_json = json.dumps(report.to_dict(), indent=2, default=str)
        score = report.health_score
        svg_dial = self._generate_svg_dial(score, "HEALTH SCORE")

        part_rows = ""
        for p in report.storage.partitions:
            bar_color = "#ef4444" if p.percent > 85 else ("#f59e0b" if p.percent > 70 else "#10b981")
            part_rows += f"""
            <tr>
                <td style="font-weight: 600;">{p.mountpoint}</td>
                <td><span class="badge badge-gray">{p.fstype}</span></td>
                <td>{p.total_formatted}</td>
                <td>{p.used_formatted}</td>
                <td>{p.free_formatted}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {p.percent}%; background-color: {bar_color};"></div>
                    </div>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">{p.percent}%</span>
                </td>
            </tr>
            """

        disk_rows = ""
        for d in report.storage.physical_disks:
            disk_rows += f"""
            <tr>
                <td style="font-weight: 600;">{d.model}</td>
                <td><span class="badge badge-gray">{d.media_type}</span></td>
                <td>{d.interface_type}</td>
                <td>{d.size_formatted}</td>
                <td><code>{d.serial_number}</code></td>
                <td><span class="badge badge-active">{d.smart_status}</span></td>
            </tr>
            """

        dimm_rows = ""
        for m in report.memory.modules:
            dimm_rows += f"""
            <tr>
                <td style="font-weight: 600;">{m.bank_label}</td>
                <td>{m.capacity_formatted}</td>
                <td><span class="badge badge-gray">{m.memory_type}</span></td>
                <td>{m.speed_mhz} MHz</td>
                <td>{m.manufacturer}</td>
                <td><code>{m.part_number}</code></td>
            </tr>
            """

        gpu_rows = ""
        for g in report.gpu.devices:
            gpu_rows += f"""
            <div class="card gpu-card" style="margin-bottom: 14px;">
                <div class="card-header">
                    <h3>🎮 {g.name}</h3>
                    <span class="badge badge-gray">{g.vendor}</span>
                </div>
                <div class="meta-grid">
                    <div><span class="label">Dedicated VRAM:</span> <span class="val">{g.vram_formatted}</span></div>
                    <div><span class="label">Driver Version:</span> <span class="val">{g.driver_version}</span></div>
                    <div><span class="label">Resolution / Refresh:</span> <span class="val">{g.resolution or 'N/A'}</span></div>
                </div>
            </div>
            """

        warn_html = ""
        if report.warnings:
            for w in report.warnings:
                w_class = "badge-red" if w.level == "CRITICAL" else ("badge-yellow" if w.level == "WARNING" else "badge-gray")
                warn_html += f"""
                <div class="warning-item">
                    <span class="badge {w_class}">{w.level}</span>
                    <span class="badge badge-gray">{w.category}</span>
                    <strong style="margin-left: 8px;">{w.title}</strong>
                    <p style="margin: 6px 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">{w.description}</p>
                </div>
                """
        else:
            warn_html = "<div class='warning-item' style='border-left-color: var(--accent-btn);'><span class='badge badge-active'>HEALTHY</span> <strong>All system checks passed with optimal parameters!</strong></div>"

        net_rows = ""
        for n in report.network.interfaces:
            if n.is_up or n.ipv4:
                status_badge = '<span class="badge badge-active">UP</span>' if n.is_up else '<span class="badge badge-gray">DOWN</span>'
                ips = ", ".join(n.ipv4) if n.ipv4 else "N/A"
                speed = f"{n.speed_mbps} Mbps" if n.speed_mbps > 0 else "Dynamic"
                net_rows += f"""
                <tr>
                    <td style="font-weight: 600;">{n.name}</td>
                    <td>{status_badge}</td>
                    <td><code>{n.mac_address}</code></td>
                    <td>{ips}</td>
                    <td>{speed}</td>
                </tr>
                """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardware Gauntlet Report - {report.system.hostname}</title>
    <style>
        :root {{
            --bg-color: #09090b;
            --surface-color: #111114;
            --surface-card: #16161a;
            --surface-border: #27272e;
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-btn: #ffffff;
            --accent-btn-text: #09090b;
            --dial-active: #ffffff;
            --dial-inactive: #27272e;
            --card-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        [data-theme="light"] {{
            --bg-color: #f5f5f7;
            --surface-color: #ffffff;
            --surface-card: #ffffff;
            --surface-border: #e5e5ea;
            --text-primary: #09090b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --accent-btn: #09090b;
            --accent-btn-text: #ffffff;
            --dial-active: #09090b;
            --dial-inactive: #e2e8f0;
            --card-shadow: 0 4px 20px rgba(0,0,0,0.06);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-primary); line-height: 1.6; padding: 24px; transition: background 0.2s, color 0.2s; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            padding: 24px 32px;
            border-radius: 20px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
        }}
        .header-title-box {{ display: flex; align-items: center; gap: 18px; }}
        .header-logo {{ width: 54px; height: 54px; border-radius: 12px; }}
        .header-title h1 {{ font-size: 1.7rem; font-weight: 800; letter-spacing: 0.5px; }}
        .header-title p {{ color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; }}
        .actions {{ display: flex; gap: 10px; }}
        
        button.btn {{
            background: var(--surface-card);
            color: var(--text-primary);
            border: 1px solid var(--surface-border);
            padding: 10px 20px;
            border-radius: 24px;
            font-weight: 700;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        button.btn:hover {{ filter: brightness(1.15); }}
        button.btn-primary {{ background: var(--accent-btn); color: var(--accent-btn-text); border: 1px solid var(--accent-btn); }}

        /* Top Hero Layout */
        .hero-grid {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media (max-width: 860px) {{
            .hero-grid {{ grid-template-columns: 1fr; }}
            header {{ flex-direction: column; gap: 16px; align-items: flex-start; }}
        }}

        .dial-card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 20px;
            padding: 24px;
            text-align: center;
            box-shadow: var(--card-shadow);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .dial-card .card-title {{ font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-primary); margin-bottom: 4px; align-self: flex-start; }}
        .dial-card .card-sub {{ font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 12px; align-self: flex-start; }}
        
        .dial-svg {{ margin: 0 auto; display: block; }}
        .dial-val {{ font-size: 28px; font-weight: 800; fill: var(--text-primary); }}
        .dial-sub {{ font-size: 10px; font-weight: 800; fill: var(--text-secondary); letter-spacing: 1px; }}
        .dial-title {{ font-size: 9px; font-weight: 800; fill: var(--text-muted); letter-spacing: 1px; }}

        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        @media (max-width: 600px) {{
            .grid-cards {{ grid-template-columns: 1fr; }}
        }}
        .stat-card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 18px;
            padding: 20px;
            box-shadow: var(--card-shadow);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .stat-card h4 {{ color: var(--text-secondary); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; font-weight: 700; }}
        .stat-card .val {{ font-size: 1.25rem; font-weight: 800; color: var(--text-primary); }}
        .stat-card .sub {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }}

        .card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
        }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
        .card-header h3 {{ font-size: 1.15rem; font-weight: 800; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }}

        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ background: var(--surface-card); color: var(--text-primary); padding: 12px 16px; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; border-bottom: 1px solid var(--surface-border); }}
        td {{ padding: 12px 16px; border-bottom: 1px solid var(--surface-border); font-size: 0.9rem; color: var(--text-primary); }}
        tr:hover td {{ background: rgba(125,125,125,0.04); }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-active {{ background: var(--accent-btn); color: var(--accent-btn-text); }}
        .badge-gray {{ background: var(--surface-card); color: var(--text-secondary); border: 1px solid var(--surface-border); }}
        .badge-yellow {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }}

        .progress-bar {{
            background: var(--surface-card);
            border: 1px solid var(--surface-border);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            display: inline-block;
            width: 80px;
            vertical-align: middle;
            margin-right: 8px;
        }}
        .progress-fill {{ height: 100%; }}

        .warning-item {{
            background: var(--surface-card);
            border: 1px solid var(--surface-border);
            border-left: 4px solid var(--accent-btn);
            padding: 14px 18px;
            border-radius: 0 12px 12px 0;
            margin-bottom: 12px;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-top: 12px;
        }}
        .meta-grid .label {{ color: var(--text-secondary); font-size: 0.8rem; display: block; font-weight: 600; text-transform: uppercase; }}
        .meta-grid .val {{ color: var(--text-primary); font-weight: 700; font-size: 0.95rem; }}
        code {{ background: var(--surface-card); border: 1px solid var(--surface-border); padding: 3px 8px; border-radius: 6px; color: var(--text-primary); font-family: monospace; font-size: 0.85rem; }}

        footer {{ text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 32px; padding: 16px; }}
        @media print {{ body {{ background: #fff; color: #000; }} header, .stat-card, .card {{ border: 1px solid #ccc; }} .actions {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title-box">
                <img src="data:image/png;base64,{LOGO_WHITE_B64}" class="header-logo" alt="Hardware Gauntlet Logo" />
                <div class="header-title">
                    <h1>YOUR SYSTEM — HARDWARE GAUNTLET</h1>
                    <p>Host: <strong>{report.system.hostname}</strong> • Scan Duration: {report.scan_duration_seconds}s • Timestamp: {report.system.timestamp}</p>
                </div>
            </div>
            <div class="actions">
                <button class="btn" onclick="toggleTheme()" id="themeBtn">☀️ Light Mode</button>
                <button class="btn btn-primary" onclick="window.print()">Print / Save PDF</button>
                <button class="btn" onclick="downloadJSON()">Export JSON</button>
            </div>
        </header>

        <!-- Top Hero with Thermostat Radial Dial -->
        <div class="hero-grid">
            <div class="dial-card">
                <div class="card-title">CARD 01 — SYSTEM HEALTH</div>
                <div class="card-sub">Real-time hardware integrity rating</div>
                {svg_dial}
            </div>
            <div class="grid-cards">
                <div class="stat-card">
                    <h4>CARD 02 — Operating System</h4>
                    <div class="val">{report.system.os_name}</div>
                    <div class="sub">Kernel: {report.system.kernel} ({report.system.boot_mode})</div>
                </div>
                <div class="stat-card">
                    <h4>CARD 03 — Processor (CPU)</h4>
                    <div class="val">{report.cpu.model.split()[0]} {report.cpu.model.split()[1] if len(report.cpu.model.split()) > 1 else ''}</div>
                    <div class="sub">{report.cpu.physical_cores} Cores / {report.cpu.logical_cores} Threads @ {format_hz(report.cpu.max_clock_mhz)}</div>
                </div>
                <div class="stat-card">
                    <h4>CARD 04 — Memory (RAM)</h4>
                    <div class="val">{format_bytes(report.memory.total_bytes)}</div>
                    <div class="sub">{report.memory.percent}% Used ({len(report.memory.modules)} DIMM modules)</div>
                </div>
                <div class="stat-card">
                    <h4>CARD 05 — Security & Boot</h4>
                    <div class="val">{'Secure Boot OK' if report.security.secure_boot else 'Secure Boot OFF'}</div>
                    <div class="sub">TPM: {'Active' if report.security.tpm_present else 'None'} | VT-x/AMD-V: {'Active' if report.security.virtualization_enabled else 'Disabled'}</div>
                </div>
            </div>
        </div>

        <!-- Health Findings -->
        <div class="card">
            <div class="card-header">
                <h3>🔍 HARDWARE AUDIT FINDINGS & ALERTS —</h3>
            </div>
            {warn_html}
        </div>

        <!-- CPU & Motherboard -->
        <div class="card">
            <div class="card-header">
                <h3>🧠 PROCESSOR & MOTHERBOARD SPECIFICATIONS —</h3>
            </div>
            <div class="meta-grid">
                <div><span class="label">CPU Full Model</span><span class="val">{report.cpu.model}</span></div>
                <div><span class="label">CPU Architecture</span><span class="val">{report.cpu.architecture}</span></div>
                <div><span class="label">Physical / Logical Cores</span><span class="val">{report.cpu.physical_cores} Cores / {report.cpu.logical_cores} Threads</span></div>
                <div><span class="label">L2 / L3 Cache</span><span class="val">L2: {report.cpu.cache_l2} | L3: {report.cpu.cache_l3}</span></div>
                <div><span class="label">Motherboard Vendor</span><span class="val">{report.motherboard.manufacturer}</span></div>
                <div><span class="label">Motherboard Model</span><span class="val">{report.motherboard.product_name}</span></div>
                <div><span class="label">BIOS Version & Date</span><span class="val">{report.motherboard.bios_version} ({report.motherboard.bios_release_date})</span></div>
                <div><span class="label">Chassis Form Factor</span><span class="val">{report.motherboard.chassis_type}</span></div>
            </div>
        </div>

        <!-- Memory Modules -->
        <div class="card">
            <div class="card-header">
                <h3>💾 MEMORY & DIMM SLOTS —</h3>
                <span class="badge badge-gray">Total: {format_bytes(report.memory.total_bytes)}</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Slot / Locator</th>
                        <th>Capacity</th>
                        <th>Type</th>
                        <th>Speed</th>
                        <th>Manufacturer</th>
                        <th>Part Number</th>
                    </tr>
                </thead>
                <tbody>
                    {dimm_rows}
                </tbody>
            </table>
        </div>

        <!-- GPUs -->
        <div class="card">
            <div class="card-header">
                <h3>🎮 GRAPHICS ACCELERATORS —</h3>
            </div>
            {gpu_rows}
        </div>

        <!-- Storage Drives -->
        <div class="card">
            <div class="card-header">
                <h3>💽 PHYSICAL STORAGE DISKS —</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Drive Model</th>
                        <th>Media</th>
                        <th>Interface</th>
                        <th>Capacity</th>
                        <th>Serial</th>
                        <th>Health</th>
                    </tr>
                </thead>
                <tbody>
                    {disk_rows}
                </tbody>
            </table>
        </div>

        <!-- Partitions -->
        <div class="card">
            <div class="card-header">
                <h3>📁 MOUNTED FILESYSTEMS & PARTITIONS —</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Mountpoint</th>
                        <th>Filesystem</th>
                        <th>Total</th>
                        <th>Used</th>
                        <th>Free</th>
                        <th>Utilization</th>
                    </tr>
                </thead>
                <tbody>
                    {part_rows}
                </tbody>
            </table>
        </div>

        <!-- Network Adapters -->
        <div class="card">
            <div class="card-header">
                <h3>🌐 ACTIVE NETWORK INTERFACES —</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Interface</th>
                        <th>Status</th>
                        <th>MAC Address</th>
                        <th>IP Address</th>
                        <th>Link Speed</th>
                    </tr>
                </thead>
                <tbody>
                    {net_rows}
                </tbody>
            </table>
        </div>

        <footer>
            Generated by <strong>Hardware Gauntlet v1.0.0</strong> • Pure Local System Hardware Scanner
        </footer>
    </div>

    <script id="report-data" type="application/json">
    {report_json}
    </script>

    <script>
    function toggleTheme() {{
        const doc = document.documentElement;
        const btn = document.getElementById('themeBtn');
        if (doc.getAttribute('data-theme') === 'light') {{
            doc.removeAttribute('data-theme');
            btn.innerText = '☀️ Light Mode';
        }} else {{
            doc.setAttribute('data-theme', 'light');
            btn.innerText = '🌙 Dark Mode';
        }}
    }}

    function downloadJSON() {{
        const data = document.getElementById('report-data').textContent;
        const blob = new Blob([data], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'hardware-gauntlet-report.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }}
    </script>
</body>
</html>"""

    def write_file(self, report: HardwareReport, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_html(report))
