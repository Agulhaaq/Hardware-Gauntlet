# ⚡ Hardware Gauntlet

> **Universal Cross-Platform Hardware Scanner & Diagnostic Suite for Windows, macOS, and Linux.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Build & Release](https://github.com/Agulhaaq/Hardware-Gauntlet/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/Agulhaaq/Hardware-Gauntlet/actions)

Hardware Gauntlet is a high-performance system hardware audit and diagnostic suite that runs as an **instant, dedicated single-instance desktop application** across Windows, macOS, and Linux without external web servers or localhost dependencies.

---

## ⚡ Dedicated Single-Instance Execution

Hardware Gauntlet is engineered strictly for **single-instance standalone execution**:
- **Strict Single-Instance Guard**: Only **1 instance** of Hardware Gauntlet is allowed to run at a time. If an attempt is made to launch another instance, the active window is automatically restored from minimized state and brought directly to the foreground.
- **Zero Installation Required**: Pure in-memory standalone operation. Leaves zero temporary files, requires no registry entries, and modifies no operating system directories.
- **100% Offline & Private**: Zero background network requests, zero telemetry, and pure local diagnostic performance.

| Mode | Windows | Linux / macOS | What Happens |
| :--- | :--- | :--- | :--- |
| **🚀 Standalone Portable GUI** | Double-click `HardwareGauntlet.exe`<br>or `Run-Portable.bat` | `./run-portable.sh` | Opens the standalone desktop UI. If already running, focuses the existing instance. |
| **🎛️ Terminal Launcher** | Double-click `Run-HardwareGauntlet.bat` | `./run-portable.sh` | Interactive prompt to launch the single GUI instance or run terminal CLI diagnostics. |

---

### ⚡ Pure Standalone & Portable Architecture

Hardware Gauntlet is 100% portable and requires zero installation:
- **Zero Registry Bloat**: Does not register uninstaller entries or modify system registry hives.
- **Self-Contained Executable**: Single standalone `.exe` with all dependencies, assets, and diagnostic engines bundled in-memory.
- **Single-Instance Enforcement**: Re-launching `HardwareGauntlet.exe` automatically detects the active instance and brings it directly to the foreground.

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

- **🔒 Strict Single-Instance Enforcement**: Named Win32 Mutex ensures only 1 application instance runs at a time. Launching a second instance automatically activates, un-minimizes, and focuses the running window.
- **⚡ On-Demand Manual Scan**: Complete user control — scans never auto-fire on launch; the application opens in a clean standby state ready for your explicit `▶ Run Full Scan` trigger.
- **🔥 Hardware Stress & Thermal Stability Engine**:
  - **Multi-Core CPU Torture**: Full load on all logical cores with floating-point calculations and SHA-256 iterations.
  - **RAM Bit-Flip Integrity**: Allocates test pattern buffers (`0xAA`, `0x55`, `0x00`, `0xFF`) and verifies against memory cell decay and bit corruption.
  - **Disk Sequential I/O**: Measures sustained sequential Write and Read speeds in MB/s.
  - **Thermal & Throttling Monitor**: Live GPU temperatures (`nvidia-smi`), clock frequency throttling, and stability verdicts (`PASSED` vs `FAILED`).
  - **Windows Benchmark Shortcuts**: 1-click execution for `mdsched.exe` (Windows Memory Diagnostic), `perfmon.exe /report`, `winsat.exe`, and `dxdiag.exe`.
- **⚡ Zero Installation Required**: 100% portable standalone executable. Leaves zero temporary residue, creates no registry keys, requires no installation, and runs directly from anywhere (USB drive, Desktop, Downloads).
- **🧠 Deep CPU Telemetry**: Cores (physical/logical), base & max frequencies, L1/L2/L3 cache sizes, architecture, instruction sets (AVX, AVX2, SSE4.2, AES-NI), and real-time utilization.
- **📊 Motherboard & BIOS Audit**: Manufacturer, board model, revision, serial number, BIOS vendor, version, release date, and chassis form factor.
- **💾 Memory (RAM) & DIMM Slots**: Total & used RAM, swap/pagefile, individual DIMM slot labels, module capacity, speed (MHz), memory technology (DDR4, DDR5, LPDDR5), manufacturer, and part numbers.
- **🎮 Dedicated & Integrated GPUs**: GPU model, vendor, dedicated VRAM, driver version, display resolutions, and refresh rates (including NVIDIA `nvidia-smi` integration).
- **💽 Physical Disks & NVMe Health**: Physical drive model, bus type (NVMe, SATA, USB), media type (SSD/HDD), serial numbers, SMART status, and partition filesystem usage with visual bars.
- **🌐 Network Adapters**: MAC addresses, IPv4 & IPv6 addresses, interface status, link speed (Mbps), and Wi-Fi identification.
- **🔒 Hardware Security Checks**: UEFI Secure Boot state, TPM 2.0 presence and firmware version, and Hardware Virtualization (VT-x / AMD-V) status.
- **🔋 Battery & Power Diagnostics**: Laptop battery percentage, AC adapter status, charge cycle counts, and capacity degradation.
- **🎯 Intelligent Health Score (0-100)**: Evaluates overall hardware health, flags mismatched memory speeds, asymmetrical RAM capacity, critical disk usage, or disabled firmware security.
- **🍱 Bento-Box Modular Studio (Concept 3 Layout)**:
  - Ergonomic modular card grid displaying thermal & clock dynamics, real-time wave telemetries, memory allocation bars, SSD wear, and actionable audit findings.
  - 8-tab studio suite: `Overview`, `Stress Test`, `CPU & Board`, `Memory`, `Graphics`, `Storage`, `Security`, and `Utilities`.
- **⚡ In-Place Update Channel & Hot-Patch Engine**:
  - Push and pull in-place upgrades without replacing your standalone executable or installer.
  - Channels supported: `Stable`, `Beta`, and `Nightly` with remote JSON manifests and SHA-256 integrity checks.
  - Atomic zip patch extraction with live dynamic module reloading into Python's runtime path.
  - 1-click rollback back to factory binary state.
- **🧹 OS Deep Storage Hygiene & Toolchains**:
  - Cleans Windows Component Store (WinSxS), stale driver backup stores, volume shadow copies, and hibernation file overhead.
  - Detects and clears multi-gigabyte developer caches: `.pip`, `.npm`, `.cargo`, `.nuget`, `.m2`, `Docker`, and `yarn`.
- **🩺 Hardware Health & Physical Maintenance Guides**:
  - Real-time NVMe & SSD lifetime write endurance calculations (TBW).
  - Physical dust, thermal paste degradation, fan airflow clearance, and port contact cleaning checklists.
- **⚡ Startup & Background Service Tuner**:
  - Audits registry run keys, startup folders, and background Windows services.
  - Measures system boot impact and optimizes high-overhead background processes.
- **🎨 QK Brand Identity & Dual Theme Support**:
  - Stark brutalist monochrome cyber aesthetic with razor-sharp contrast.
  - Instant toggling between `🌙 Dark Mode` (obsidian void `#08080a`, slate `#25252e`, pure white `#ffffff`) and `☀️ Light Mode` (paper `#f5f5f7`, pure black `#09090b`).
- **📄 Multi-Format Reporting**:
  - Interactive styled terminal dashboard (`rich` + auto ASCII fallback)
  - Standalone single-file HTML audit report (interactive with print/PDF export and embedded logo)
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
├── assets/                   # Multi-resolution icons & brand assets
│   ├── app.ico               # Windows multi-resolution PE icon (16..256px)
│   ├── app.png               # High-res obsidian squircle app badge
│   ├── logo_white_*.png      # White monochrome monogram variants
│   └── logo_black_*.png      # Black monochrome monogram variants
├── hwscan/
│   ├── __init__.py           # Package version & metadata
│   ├── __main__.py           # python -m hwscan entrypoint
│   ├── cli.py                # Command-line argument parsing
│   ├── gui.py                # Bento-Box Studio Tkinter GUI & theme engine
│   ├── assets_data.py        # In-memory base64 logo fallbacks
│   ├── core/
│   │   ├── models.py         # Hardware dataclasses & JSON serializers
│   │   ├── system_info.py    # Master engine & health scoring
│   │   ├── stress_test.py    # Multi-core CPU, RAM pattern, and disk throughput engine
│   │   ├── instance_guard.py # Single-instance mutex and foreground window manager
│   │   ├── update_channel.py # In-place update channel & hot-patch engine
│   │   ├── cleanup.py        # Basic temp, memory, and DNS resolver cleanup
│   │   ├── deep_cleanup.py   # WinSxS, driver store, and developer cache hygiene
│   │   ├── hardware_health.py # SSD TBW endurance & thermal stress analytics
│   │   ├── physical_maintenance.py # Dust, thermal paste, and cleaning checklists
│   │   ├── startup_service_tuner.py # Startup run keys & background services
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
│   ├── install.ps1           # 1-liner portable Windows runner (zero install)
│   ├── install.sh            # 1-liner portable Unix runner (zero install)
│   └── download_page.html    # Standalone static download landing page
├── scripts/
│   ├── build_branding_assets.py # Multi-resolution brand asset generator
│   └── capture_current_ui.py    # Automated headless UI capture harness
├── tests/                    # 91 comprehensive automated pytest tests
├── .github/
│   └── workflows/
│       └── build-and-release.yml # Multi-OS CI/CD build matrix
├── HardwareGauntlet.spec     # Windows PyInstaller UPX spec
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
