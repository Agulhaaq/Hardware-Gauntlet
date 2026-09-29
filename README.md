# ⚡ Hardware Gauntlet

> **Universal Cross-Platform Hardware Scanner & Diagnostic Suite for Windows, macOS, and Linux.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Build & Release](https://github.com/Agulhaaq/Hardware-Gauntlet/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/Agulhaaq/Hardware-Gauntlet/actions)

Hardware Gauntlet is a high-performance system hardware audit and diagnostic suite that runs as a **full permanent installed desktop application** or as an **instant one-off portable instance** across Windows, macOS, and Linux without external web servers or localhost dependencies.

---

## ⚡ Two Ways to Run: "Just Run" or "Install as Application"

Hardware Gauntlet provides total flexibility: you can **run it as a portable one-off instance without installing anything**, or **install it permanently to your operating system**.

| Mode | Windows | Linux / macOS | What Happens |
| :--- | :--- | :--- | :--- |
| **🚀 Option 1: Just Run (One-Off Instance)** | Double-click `Run-Portable.bat`<br>or `HardwareGauntlet.exe` | `./run-portable.sh` | **Zero installation.** Runs instantly in-memory. Leaves no traces, writes no registry keys, and requires no admin rights. |
| **📦 Option 2: Install as Application** | Double-click `Setup-HardwareGauntlet.exe`<br>or `Install-HardwareGauntlet.bat` | `bash installer/install-linux.sh`<br>`bash installer/install-macos.sh` | **Permanent installation.** Adds to Start Menu, creates Desktop shortcut, registers in Windows Settings > Installed Apps, and adds `hwscan` to User `PATH`. |
| **🎛️ Interactive Choice Menu** | Double-click `Run-HardwareGauntlet.bat` | `./run-portable.sh` | Terminal launcher giving you a 1-click prompt to select between Portable, Installer, or CLI mode. |

---

### 🪟 Windows Details

- **⚡ Just Run (Portable)**:
  - Simply double-click `Run-Portable.bat` or `HardwareGauntlet.exe`.
  - The native Tkinter GUI opens immediately and scans hardware in parallel (~2.7s).
  - Can be carried on a USB drive or run from any folder without setup.

- **📦 Install as Full Application**:
  - **GUI Setup Wizard**: Run `Setup-HardwareGauntlet.exe` (includes both a "⚡ Just Run Now" button and a guided install flow).
  - **1-Click Batch Installer**: Double-click `Install-HardwareGauntlet.bat` or run:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\installer\install-windows.ps1
    ```
  - *Integration Details:*
    - Installs to `%LOCALAPPDATA%\Programs\HardwareGauntlet`
    - Start Menu shortcut (searchable in Windows Search)
    - Desktop shortcut with high-resolution icon
    - Registered in **Windows Settings > Apps > Installed apps** (clean 1-click uninstall)
    - Adds `hwscan` to User `PATH` for instant CLI access anywhere

---

### 🐧 Linux & 🍎 macOS Details

- **⚡ Just Run (Portable)**:
  ```bash
  ./run-portable.sh
  ```
- **📦 Permanent Installation**:
  - **Linux**: `bash installer/install-linux.sh` (installs binary to `~/.local/bin`, creates `.desktop` menu shortcut)
  - **macOS**: `bash installer/install-macos.sh` (installs `Hardware Gauntlet.app` into `/Applications` with Spotlight search)

---

## 🚀 Instant 1-Command CLI Run Per Operating System

Run directly in your terminal without manual cloning or configuration:

### 🪟 Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.ps1 | iex
```

### 🍎 macOS (Apple Silicon & Intel)
```bash
curl -fsSL https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.sh | bash
```

### 🐧 Linux (Ubuntu, Debian, Fedora, Arch, RHEL)
```bash
curl -fsSL https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.sh | bash
```

### 🐍 Standard Python / Pip
```bash
pip install hwscan
hwscan
```

---

## 🌟 Key Capabilities

- **🧠 Deep CPU Telemetry**: Cores (physical/logical), base & max frequencies, L1/L2/L3 cache sizes, architecture, instruction sets (AVX, AVX2, SSE4.2, AES-NI), and real-time utilization.
- **📊 Motherboard & BIOS Audit**: Manufacturer, board model, revision, serial number, BIOS vendor, version, release date, and chassis form factor.
- **💾 Memory (RAM) & DIMM Slots**: Total & used RAM, swap/pagefile, individual DIMM slot labels, module capacity, speed (MHz), memory technology (DDR4, DDR5, LPDDR5), manufacturer, and part numbers.
- **🎮 Dedicated & Integrated GPUs**: GPU model, vendor, dedicated VRAM, driver version, display resolutions, and refresh rates (including NVIDIA `nvidia-smi` integration).
- **💽 Physical Disks & NVMe Health**: Physical drive model, bus type (NVMe, SATA, USB), media type (SSD/HDD), serial numbers, SMART status, and partition filesystem usage with visual bars.
- **🌐 Network Adapters**: MAC addresses, IPv4 & IPv6 addresses, interface status, link speed (Mbps), and Wi-Fi identification.
- **🔒 Hardware Security Checks**: UEFI Secure Boot state, TPM 2.0 presence and firmware version, and Hardware Virtualization (VT-x / AMD-V) status.
- **🔋 Battery & Power Diagnostics**: Laptop battery percentage, AC adapter status, charge cycle counts, and capacity degradation.
- **🎯 Intelligent Health Score (0-100)**: Evaluates overall hardware health, flags mismatched memory speeds, asymmetrical RAM capacity, critical disk usage, or disabled firmware security.
- **📄 Multi-Format Reporting**:
  - Interactive styled terminal dashboard (`rich` + auto ASCII fallback)
  - Standalone single-file HTML audit report (interactive with print/PDF export)
  - Machine-readable JSON
  - GitHub-flavored Markdown
- **🌐 Built-in Web Server & Download Portal**: Run `hwscan --web` to launch a browser dashboard that detects client OS and serves custom downloads.

---

## 🖥️ Command-Line Interface (CLI)

```bash
# Standard styled terminal scan
hwscan

# Detailed scan including peripherals and all network adapters
hwscan --full

# Generate an interactive HTML report
hwscan --html my-report.html

# Export machine-readable JSON (or to stdout with -)
hwscan --json hardware-report.json
hwscan --json -

# Export GitHub Markdown report
hwscan --markdown system-specs.md

# Quick health check (exit code 0 if healthy, 1 if critical warnings)
hwscan --health

# Launch embedded Web Portal & Multi-OS Download Center
hwscan --web --port 8080
```

---

## 🌐 Embedded Web Portal & Download Center

Start the local server:
```bash
hwscan --web --port 8080
```
Open [http://localhost:8080](http://localhost:8080) in any browser to:
1. Automatically detect the visiting device's operating system.
2. Download operating-system-tailored executables and install scripts.
3. Inspect live real-time hardware gauges and system health.
4. Export offline HTML and JSON reports on the fly.

---

## 📦 Project Architecture

```
Hardware-Gauntlet/
├── hwscan/
│   ├── __init__.py           # Package version & metadata
│   ├── __main__.py           # python -m hwscan entrypoint
│   ├── cli.py                # Command-line argument parsing
│   ├── core/
│   │   ├── models.py         # Hardware dataclasses & JSON serializers
│   │   ├── system_info.py    # Master engine & health scoring
│   │   └── utils.py          # Cross-platform subprocess & formatters
│   ├── scanners/
│   │   ├── base.py           # BaseScanner interface
│   │   ├── system.py         # OS, kernel, uptime, boot mode
│   │   ├── cpu.py            # Processor specs & features
│   │   ├── memory.py         # RAM, DIMM slots, swap
│   │   ├── motherboard.py    # Motherboard & BIOS
│   │   ├── gpu.py            # GPU adapters, VRAM, drivers
│   │   ├── storage.py        # Physical drives (NVMe/SSD) & partitions
│   │   ├── network.py        # Network adapters, MACs, IPs
│   │   ├── battery.py        # Battery health & cycle count
│   │   ├── peripherals.py    # USB, audio controllers, bluetooth
│   │   └── security.py       # Secure Boot, TPM 2.0, virtualization
│   ├── reporters/
│   │   ├── console.py        # Rich terminal UI & ASCII fallback
│   │   ├── json_reporter.py  # Structured JSON exporter
│   │   ├── markdown.py       # Markdown exporter
│   │   └── html_reporter.py  # Standalone interactive HTML report
│   └── web/
│       └── server.py         # HTTP server & Multi-OS download portal
├── distribution/
│   ├── install.ps1           # 1-liner Windows installer
│   ├── install.sh            # 1-liner Linux/macOS installer
│   └── download_page.html    # Standalone static download landing page
├── .github/
│   └── workflows/
│       └── build-and-release.yml  # Multi-OS CI/CD build matrix
├── build.py                  # Standalone PyInstaller compiler script
├── pyproject.toml            # PEP 518/621 build configuration
├── setup.py                  # Setuptools configuration
├── requirements.txt          # Core dependencies
└── README.md                 # Documentation
```

---

## 🛠️ Compiling Standalone Executables Locally

To compile a single-file executable for your current OS:

```bash
python build.py
```

The compiled binary will be placed in the `dist/` directory:
- **Windows**: `dist/hwscan-windows-x64.exe`
- **macOS**: `dist/hwscan-macos-universal`
- **Linux**: `dist/hwscan-linux-x64`

---

## 🤖 GitHub CI/CD Multi-OS Matrix

The repository includes a ready-to-use GitHub Actions workflow (`.github/workflows/build-and-release.yml`).

When you push a git tag (e.g., `v1.0.0`):
1. Runs three parallel builders on `windows-latest`, `ubuntu-latest`, and `macos-latest`.
2. Packages standalone self-contained binaries for each platform.
3. Automatically publishes a GitHub Release with all three executables attached for direct download!

---

## 📄 License

MIT License. Free to use, modify, and distribute for personal and commercial purposes.
