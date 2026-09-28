"""Interactive standalone HTML Diagnostic Report Generator for Hardware Gauntlet."""

import json
from hwscan.core.models import HardwareReport
from hwscan.core.utils import format_bytes, format_hz


class HTMLReporter:
    """Generates a modern, self-contained interactive HTML hardware audit report."""

    def to_html(self, report: HardwareReport) -> str:
        report_json = json.dumps(report.to_dict(), indent=2, default=str)
        score = report.health_score
        score_class = "score-high" if score >= 85 else ("score-med" if score >= 70 else "score-low")

        # Partitions rows
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
                    <span style="font-size: 0.8rem; color: #94a3b8;">{p.percent}%</span>
                </td>
            </tr>
            """

        # Disks rows
        disk_rows = ""
        for d in report.storage.physical_disks:
            disk_rows += f"""
            <tr>
                <td style="font-weight: 600;">{d.model}</td>
                <td><span class="badge badge-blue">{d.media_type}</span></td>
                <td>{d.interface_type}</td>
                <td>{d.size_formatted}</td>
                <td><code>{d.serial_number}</code></td>
                <td><span class="badge badge-green">{d.smart_status}</span></td>
            </tr>
            """

        # DIMM rows
        dimm_rows = ""
        for m in report.memory.modules:
            dimm_rows += f"""
            <tr>
                <td style="font-weight: 600;">{m.bank_label}</td>
                <td>{m.capacity_formatted}</td>
                <td><span class="badge badge-purple">{m.memory_type}</span></td>
                <td>{m.speed_mhz} MHz</td>
                <td>{m.manufacturer}</td>
                <td><code>{m.part_number}</code></td>
            </tr>
            """

        # GPU rows
        gpu_rows = ""
        for g in report.gpu.devices:
            gpu_rows += f"""
            <div class="card gpu-card">
                <div class="card-header">
                    <h3>🎮 {g.name}</h3>
                    <span class="badge badge-purple">{g.vendor}</span>
                </div>
                <div class="meta-grid">
                    <div><span class="label">Dedicated VRAM:</span> <span class="val">{g.vram_formatted}</span></div>
                    <div><span class="label">Driver Version:</span> <span class="val">{g.driver_version}</span></div>
                    <div><span class="label">Resolution / Refresh:</span> <span class="val">{g.resolution or 'N/A'}</span></div>
                </div>
            </div>
            """

        # Warnings cards
        warn_html = ""
        if report.warnings:
            for w in report.warnings:
                w_class = "badge-red" if w.level == "CRITICAL" else ("badge-yellow" if w.level == "WARNING" else "badge-blue")
                warn_html += f"""
                <div class="warning-item">
                    <span class="badge {w_class}">{w.level}</span>
                    <span class="badge badge-gray">{w.category}</span>
                    <strong style="margin-left: 8px;">{w.title}</strong>
                    <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{w.description}</p>
                </div>
                """
        else:
            warn_html = "<div class='warning-item' style='border-left-color: #10b981;'><span class='badge badge-green'>HEALTHY</span> <strong>All system checks passed with optimal parameters!</strong></div>"

        # Active Network interfaces
        net_rows = ""
        for n in report.network.interfaces:
            if n.is_up or n.ipv4:
                status_badge = '<span class="badge badge-green">UP</span>' if n.is_up else '<span class="badge badge-gray">DOWN</span>'
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

        # Build full HTML
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardware Gauntlet Report - {report.system.hostname}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --surface-color: #111827;
            --surface-border: #1f2937;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-cyan: #06b6d4;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-primary); line-height: 1.6; padding: 24px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
            backdrop-filter: blur(10px);
            border: 1px solid var(--surface-border);
            padding: 24px 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        .header-title h1 {{ font-size: 1.8rem; font-weight: 800; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header-title p {{ color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px; }}
        .header-score {{ display: flex; align-items: center; gap: 16px; }}
        
        .score-box {{
            text-align: center;
            padding: 12px 20px;
            border-radius: 12px;
            background: rgba(0,0,0,0.3);
            border: 2px solid;
        }}
        .score-high {{ border-color: var(--accent-green); color: var(--accent-green); }}
        .score-med {{ border-color: var(--accent-yellow); color: var(--accent-yellow); }}
        .score-low {{ border-color: var(--accent-red); color: var(--accent-red); }}
        .score-box .num {{ font-size: 2.2rem; font-weight: 800; line-height: 1; }}
        .score-box .lbl {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); }}

        .actions {{ display: flex; gap: 10px; }}
        button.btn {{
            background: #1e293b;
            color: #fff;
            border: 1px solid #334155;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        button.btn:hover {{ background: #334155; border-color: #475569; }}
        button.btn-primary {{ background: linear-gradient(135deg, #2563eb, #3b82f6); border: none; }}
        button.btn-primary:hover {{ background: linear-gradient(135deg, #1d4ed8, #2563eb); }}

        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }}
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
        }}
        .stat-card h4 {{ color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
        .stat-card .val {{ font-size: 1.3rem; font-weight: 700; color: #fff; }}
        .stat-card .sub {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px; }}

        .card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
        .card-header h3 {{ font-size: 1.25rem; font-weight: 700; color: #f1f5f9; display: flex; align-items: center; gap: 8px; }}

        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ background: #1e293b; color: #94a3b8; padding: 12px 16px; font-size: 0.85rem; text-transform: uppercase; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid #1f2937; font-size: 0.95rem; }}
        tr:hover td {{ background: rgba(255,255,255,0.02); }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-green {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }}
        .badge-blue {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
        .badge-purple {{ background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.4); }}
        .badge-yellow {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-gray {{ background: rgba(148, 163, 184, 0.2); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); }}

        .progress-bar {{
            background: #1e293b;
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
            background: rgba(30, 41, 59, 0.5);
            border-left: 4px solid var(--accent-yellow);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 12px;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .meta-grid .label {{ color: var(--text-secondary); font-size: 0.85rem; display: block; }}
        .meta-grid .val {{ color: #f8fafc; font-weight: 600; font-size: 1rem; }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; font-family: monospace; font-size: 0.85rem; }}

        footer {{ text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 32px; padding: 16px; }}
        @media print {{ body {{ background: #fff; color: #000; }} header, .stat-card, .card {{ border: 1px solid #ccc; }} .actions {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>⚡ Hardware Gauntlet</h1>
                <p>Host: <strong>{report.system.hostname}</strong> • Scan: {report.system.timestamp} (Duration: {report.scan_duration_seconds}s)</p>
            </div>
            <div class="header-score">
                <div class="score-box {score_class}">
                    <div class="num">{score}</div>
                    <div class="lbl">Health Score</div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" onclick="window.print()">🖨️ Print / Save PDF</button>
                    <button class="btn" onclick="downloadJSON()">💾 Export JSON</button>
                </div>
            </div>
        </header>

        <!-- KPI Cards -->
        <div class="grid-cards">
            <div class="stat-card">
                <h4>Operating System</h4>
                <div class="val">{report.system.os_name}</div>
                <div class="sub">Kernel: {report.system.kernel} ({report.system.boot_mode})</div>
            </div>
            <div class="stat-card">
                <h4>Processor (CPU)</h4>
                <div class="val">{report.cpu.model.split()[0]} {report.cpu.model.split()[1] if len(report.cpu.model.split()) > 1 else ''}</div>
                <div class="sub">{report.cpu.physical_cores} Cores / {report.cpu.logical_cores} Threads @ {format_hz(report.cpu.max_clock_mhz)}</div>
            </div>
            <div class="stat-card">
                <h4>Memory (RAM)</h4>
                <div class="val">{format_bytes(report.memory.total_bytes)}</div>
                <div class="sub">{report.memory.percent}% Used ({len(report.memory.modules)} DIMM slots)</div>
            </div>
            <div class="stat-card">
                <h4>Security & Boot</h4>
                <div class="val">{'Secure Boot OK' if report.security.secure_boot else 'Secure Boot OFF'}</div>
                <div class="sub">TPM: {'Active' if report.security.tpm_present else 'None'} | VT-x/AMD-V: {'Active' if report.security.virtualization_enabled else 'Disabled'}</div>
            </div>
        </div>

        <!-- Health Findings -->
        <div class="card">
            <div class="card-header">
                <h3>🔍 Diagnostics & Health Findings</h3>
            </div>
            {warn_html}
        </div>

        <!-- CPU & Motherboard -->
        <div class="card">
            <div class="card-header">
                <h3>🧠 Processor & Motherboard Specifications</h3>
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
                <h3>📊 Memory & DIMM Slots</h3>
                <span class="badge badge-blue">Total: {format_bytes(report.memory.total_bytes)}</span>
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
                <h3>🎮 Graphics Adapters</h3>
            </div>
            {gpu_rows}
        </div>

        <!-- Storage Drives -->
        <div class="card">
            <div class="card-header">
                <h3>💾 Physical Storage Disks</h3>
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
                <h3>📁 Mounted Filesystems & Partitions</h3>
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
                <h3>🌐 Active Network Interfaces</h3>
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
            Generated by <strong>Hardware Gauntlet v1.0.0</strong> • Cross-Platform System Hardware Scanner
        </footer>
    </div>

    <script id="report-data" type="application/json">
    {report_json}
    </script>

    <script>
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
