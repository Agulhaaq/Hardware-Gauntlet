#!/usr/bin/env bash
# Hardware Gauntlet - Portable Run (Zero Installation)
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "    ⚡ HARDWARE GAUNTLET - ONE-OFF PORTABLE INSTANCE ⚡    "
echo "=========================================================="
echo "Starting Hardware Gauntlet immediately without installation..."
echo ""

# Check for prebuilt native binary
if [[ "$OSTYPE" == "linux"* ]] && [ -f "$DIR/dist/hwscan-linux-x64" ]; then
    "$DIR/dist/hwscan-linux-x64" "$@"
    exit 0
elif [[ "$OSTYPE" == "darwin"* ]] && [ -f "$DIR/dist/hwscan-macos-universal" ]; then
    "$DIR/dist/hwscan-macos-universal" "$@"
    exit 0
fi

# Fallback to Python environment
if command -v python3 >/dev/null 2>&1; then
    if [ "$1" == "--cli" ] || [ -z "$DISPLAY" -a -z "$WAYLAND_DISPLAY" ]; then
        python3 -m hwscan "$@"
    else
        python3 -m hwscan.gui "$@" 2>/dev/null || python3 -m hwscan "$@"
    fi
else
    echo "Error: Python 3 or prebuilt binary not found."
    exit 1
fi
