#!/usr/bin/env bash
# Hardware Gauntlet - Instant Portable Unix Runner (Zero Installation Required)
# Usage: curl -fsSL https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.sh | bash

set -e

echo "=========================================================="
echo "   ⚡ HARDWARE GAUNTLET - PORTABLE RUNNER (NO INSTALL) ⚡ "
echo "=========================================================="

if command -v python3 >/dev/null 2>&1; then
    echo "[✓] Python 3 detected. Running portable hardware audit..."
    if [ -f "hwscan/__main__.py" ]; then
        python3 -m hwscan "$@"
        exit 0
    fi
    python3 -m pip install psutil rich --quiet 2>/dev/null || true
    python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/hwscan/cli.py').read().decode())" "$@" || true
    exit 0
fi

echo "Python 3 not detected. Printing native hardware telemetry..."
uname -a
lscpu 2>/dev/null || sysctl -a machdep.cpu 2>/dev/null
