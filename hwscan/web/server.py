"""Embedded Web Server and Multi-OS Download Portal for Hardware Gauntlet."""

import os
import sys
import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.html_reporter import HTMLReporter
from hwscan.reporters.json_reporter import JSONReporter

PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardware Gauntlet - Universal Hardware Diagnostic Suite</title>
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #111827;
            --surface-hover: #1e293b;
            --border: #1f2937;
            --primary: #38bdf8;
            --accent: #818cf8;
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --green: #10b981;
            --yellow: #f59e0b;
            --red: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: var(--bg); color: var(--text); line-height: 1.6; }
        
        .hero {
            text-align: center;
            padding: 60px 20px 40px;
            background: radial-gradient(circle at 50% 20%, rgba(56, 189, 248, 0.15) 0%, transparent 60%);
            border-bottom: 1px solid var(--border);
        }
        .hero h1 { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero p { color: var(--text-dim); font-size: 1.15rem; max-width: 680px; margin: 12px auto 24px; }
        .detected-banner {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 0.95rem;
            color: #7dd3fc;
            margin-bottom: 20px;
        }

        .container { max-width: 1100px; margin: 0 auto; padding: 32px 20px; }
        
        .section-title { font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; color: #fff; text-align: center; }
        .os-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin-bottom: 48px;
        }
        .os-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            display: flex;
            flex-direction: column;
            position: relative;
            transition: transform 0.2s, border-color 0.2s;
        }
        .os-card:hover { transform: translateY(-4px); border-color: var(--primary); }
        .os-card.recommended {
            border-color: #38bdf8;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.2);
        }
        .os-card.recommended::before {
            content: 'YOUR DETECTED OS';
            position: absolute;
            top: -12px;
            left: 24px;
            background: linear-gradient(90deg, #0284c7, #2563eb);
            color: #fff;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.5px;
        }
        .os-header { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
        .os-icon { font-size: 2.2rem; }
        .os-header h3 { font-size: 1.4rem; font-weight: 700; }
        .os-sub { color: var(--text-dim); font-size: 0.85rem; }
        .os-features { list-style: none; margin: 16px 0 24px; flex-grow: 1; }
        .os-features li { margin-bottom: 8px; color: #cbd5e1; font-size: 0.9rem; display: flex; align-items: center; gap: 8px; }
        .os-features li::before { content: '✓'; color: var(--green); font-weight: bold; }

        .btn-download {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #fff;
            text-decoration: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 700;
            text-align: center;
            display: block;
            margin-bottom: 12px;
            transition: opacity 0.2s;
        }
        .btn-download:hover { opacity: 0.9; }

        .cmd-box {
            background: #090d16;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 10px 14px;
            position: relative;
            font-family: monospace;
            font-size: 0.82rem;
            color: #38bdf8;
            overflow-x: auto;
            white-space: nowrap;
        }
        .copy-btn {
            position: absolute;
            right: 6px;
            top: 6px;
            background: #1e293b;
            color: #fff;
            border: 1px solid #334155;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            cursor: pointer;
        }
        .copy-btn:hover { background: #334155; }

        /* Live Machine Preview */
        .live-preview {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 32px;
            margin-top: 32px;
        }
        .live-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .live-preview-header h2 { font-size: 1.5rem; font-weight: 700; }
        .btn-group { display: flex; gap: 10px; }
        .btn-action {
            background: #1e293b;
            color: #fff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            border: 1px solid #334155;
            transition: all 0.2s;
        }
        .btn-action:hover { background: #334155; }

        .spec-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }
        .spec-item {
            background: #090d16;
            border: 1px solid #1e293b;
            padding: 16px;
            border-radius: 10px;
        }
        .spec-lbl { color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; margin-bottom: 4px; }
        .spec-val { font-size: 1.05rem; font-weight: 600; color: #fff; }

        footer { text-align: center; color: var(--text-dim); font-size: 0.85rem; padding: 40px 0; border-top: 1px solid var(--border); }
    </style>
</head>
<body>
    <div class="hero">
        <h1>⚡ Hardware Gauntlet</h1>
        <p>The universal hardware scanning and diagnostic suite for Windows, macOS, and Linux. Zero configuration, deep telemetry, and instant health scoring.</p>
        <div id="detected-banner" class="detected-banner">
            <span>🔍 Detecting your device OS...</span>
        </div>
    </div>

    <div class="container">
        <h2 class="section-title">Download For Any Operating System</h2>

        <div class="os-grid">
            <!-- Windows Card -->
            <div id="card-windows" class="os-card">
                <div class="os-header">
                    <div class="os-icon">🪟</div>
                    <div>
                        <h3>Windows</h3>
                        <div class="os-sub">Windows 10, 11 & Server (x64 / ARM64)</div>
                    </div>
                </div>
                <ul class="os-features">
                    <li>Single standalone .exe (no Python required)</li>
                    <li>WMI & CIM deep hardware extraction</li>
                    <li>Secure Boot, TPM 2.0 & RAM DIMM audit</li>
                    <li>NVIDIA / AMD / Intel GPU telemetry</li>
                </ul>
                <a href="/install.ps1" download="install.ps1" class="btn-download">Download Windows Script</a>
                <div class="cmd-box">
                    <span>irm http://localhost:8080/install.ps1 | iex</span>
                    <button class="copy-btn" onclick="copyText('irm http://localhost:8080/install.ps1 | iex')">Copy</button>
                </div>
            </div>

            <!-- macOS Card -->
            <div id="card-macos" class="os-card">
                <div class="os-header">
                    <div class="os-icon">🍎</div>
                    <div>
                        <h3>macOS</h3>
                        <div class="os-sub">Apple Silicon (M1-M4) & Intel Macs</div>
                    </div>
                </div>
                <ul class="os-features">
                    <li>Universal binary for ARM64 & x86_64</li>
                    <li>system_profiler & IOKit hardware engine</li>
                    <li>Unified memory & Apple Neural Engine specs</li>
                    <li>Battery cycle & health condition audit</li>
                </ul>
                <a href="/install.sh" download="install.sh" class="btn-download">Download macOS Script</a>
                <div class="cmd-box">
                    <span>curl -fsSL http://localhost:8080/install.sh | bash</span>
                    <button class="copy-btn" onclick="copyText('curl -fsSL http://localhost:8080/install.sh | bash')">Copy</button>
                </div>
            </div>

            <!-- Linux Card -->
            <div id="card-linux" class="os-card">
                <div class="os-header">
                    <div class="os-icon">🐧</div>
                    <div>
                        <h3>Linux</h3>
                        <div class="os-sub">Ubuntu, Debian, Fedora, Arch, RHEL</div>
                    </div>
                </div>
                <ul class="os-features">
                    <li>Compatible with all major distributions</li>
                    <li>/proc, /sys, lsblk, lspci & dmidecode</li>
                    <li>Lightweight, zero GUI dependency required</li>
                    <li>Server & Desktop hardware audit</li>
                </ul>
                <a href="/install.sh" download="install.sh" class="btn-download">Download Linux Script</a>
                <div class="cmd-box">
                    <span>curl -fsSL http://localhost:8080/install.sh | bash</span>
                    <button class="copy-btn" onclick="copyText('curl -fsSL http://localhost:8080/install.sh | bash')">Copy</button>
                </div>
            </div>
        </div>

        <!-- Live Machine Section -->
        <div class="live-preview">
            <div class="live-preview-header">
                <div>
                    <h2>🖥️ Live Machine Hardware Monitor</h2>
                    <p style="color: var(--text-dim); font-size: 0.9rem;">Real-time scan from host: <strong>{{HOSTNAME}}</strong></p>
                </div>
                <div class="btn-group">
                    <a href="/export/html" class="btn-action">📄 Full HTML Report</a>
                    <a href="/export/json" class="btn-action">💾 JSON API</a>
                    <button onclick="refreshScan()" class="btn-action" style="cursor: pointer;">🔄 Refresh</button>
                </div>
            </div>

            <div class="spec-grid">
                <div class="spec-item">
                    <div class="spec-lbl">Host & OS</div>
                    <div class="spec-val">{{OS_NAME}}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-lbl">Processor (CPU)</div>
                    <div class="spec-val">{{CPU_MODEL}}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-lbl">Memory (RAM)</div>
                    <div class="spec-val">{{RAM_INFO}}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-lbl">Graphics (GPU)</div>
                    <div class="spec-val">{{GPU_INFO}}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-lbl">Health Score</div>
                    <div class="spec-val" style="color: var(--green);">{{HEALTH_SCORE}} / 100</div>
                </div>
                <div class="spec-item">
                    <div class="spec-lbl">Security</div>
                    <div class="spec-val">{{SECURITY_INFO}}</div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        Hardware Gauntlet • Open Source Cross-Platform Hardware Diagnostic Suite
    </footer>

    <script>
        // Detect OS and highlight recommended card
        (function() {
            const ua = window.navigator.userAgent.toLowerCase();
            const platform = window.navigator.platform ? window.navigator.platform.toLowerCase() : '';
            let detected = "Unknown";
            let targetCard = null;

            if (ua.includes("win") || platform.includes("win")) {
                detected = "Windows";
                targetCard = document.getElementById("card-windows");
            } else if (ua.includes("mac") || platform.includes("mac")) {
                detected = "macOS";
                targetCard = document.getElementById("card-macos");
            } else if (ua.includes("linux") || platform.includes("linux")) {
                detected = "Linux";
                targetCard = document.getElementById("card-linux");
            }

            const banner = document.getElementById("detected-banner");
            if (targetCard) {
                targetCard.classList.add("recommended");
                banner.innerHTML = `<span>💻 Detected: <strong>${detected}</strong> — Recommended download highlighted below!</span>`;
            } else {
                banner.innerHTML = `<span>🌐 Select your operating system below</span>`;
            }
        })();

        function copyText(txt) {
            navigator.clipboard.writeText(txt).then(() => {
                alert("Command copied to clipboard: " + txt);
            });
        }

        function refreshScan() {
            location.reload();
        }
    </script>
</body>
</html>
"""


class HardwareServerHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Hardware Gauntlet Web UI & API."""

    engine = HardwareScannerEngine()
    html_reporter = HTMLReporter()
    json_reporter = JSONReporter()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._handle_home()
        elif path == "/api/scan":
            self._handle_api_scan()
        elif path == "/export/html":
            self._handle_export_html()
        elif path == "/export/json":
            self._handle_export_json()
        elif path == "/install.ps1":
            self._handle_install_ps1()
        elif path == "/install.sh":
            self._handle_install_sh()
        else:
            self.send_error(404, "Endpoint Not Found")

    def _handle_home(self):
        report = self.engine.run_full_scan()
        html = PORTAL_HTML
        html = html.replace("{{HOSTNAME}}", report.system.hostname)
        html = html.replace("{{OS_NAME}}", f"{report.system.os_name} ({report.system.os_arch})")
        html = html.replace("{{CPU_MODEL}}", report.cpu.model)
        html = html.replace("{{RAM_INFO}}", f"{report.memory.percent}% used of {report.memory.total_bytes // (1024**3)} GB")
        gpu_str = report.gpu.devices[0].name if report.gpu.devices else "Integrated Graphics"
        html = html.replace("{{GPU_INFO}}", gpu_str)
        html = html.replace("{{HEALTH_SCORE}}", str(report.health_score))
        sec_str = "Secure Boot OK" if report.security.secure_boot else "Standard"
        html = html.replace("{{SECURITY_INFO}}", sec_str)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _handle_api_scan(self):
        report = self.engine.run_full_scan()
        data = self.json_reporter.to_json(report)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def _handle_export_html(self):
        report = self.engine.run_full_scan()
        html = self.html_reporter.to_html(report)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Disposition", f"attachment; filename=hardware-report-{report.system.hostname}.html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _handle_export_json(self):
        report = self.engine.run_full_scan()
        data = self.json_reporter.to_json(report)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", f"attachment; filename=hardware-report-{report.system.hostname}.json")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def _handle_install_ps1(self):
        script = """# Hardware Gauntlet Standalone Portable Windows Runner (Zero Installation)
Write-Host "Starting Standalone Portable Hardware Gauntlet..." -ForegroundColor Cyan
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pip install psutil rich --quiet
    python -m hwscan
} else {
    Write-Host "Python not found. Running native PowerShell hardware scanner..." -ForegroundColor Yellow
    Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List
    Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer | Format-List
    Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion | Format-List
}
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(script.encode("utf-8"))

    def _handle_install_sh(self):
        script = """#!/usr/bin/env bash
# Hardware Gauntlet Standalone Portable Unix Runner (Zero Installation)
echo "=== Starting Standalone Portable Hardware Gauntlet ==="
if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install psutil rich --quiet 2>/dev/null || true
    python3 -m hwscan
else
    echo "Python 3 not found. Printing core hardware telemetry..."
    uname -a
    lscpu 2>/dev/null || sysctl -a machdep.cpu 2>/dev/null
fi
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(script.encode("utf-8"))


def start_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the Hardware Gauntlet web portal and API server."""
    server = HTTPServer((host, port), HardwareServerHandler)
    print(f"[*] Hardware Gauntlet Web Portal running at http://{host}:{port}/")
    print(f"[*] View live dashboard and OS downloads in your browser.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
        server.server_close()
