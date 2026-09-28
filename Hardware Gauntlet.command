#!/usr/bin/env bash
# Hardware Gauntlet - Double-clickable macOS Finder Application Launcher

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Launching Hardware Gauntlet..."

if [ -f "$DIR/dist/hwscan-macos-universal" ]; then
    "$DIR/dist/hwscan-macos-universal" --gui
elif command -v python3 >/dev/null 2>&1; then
    python3 -m hwscan --gui
else
    echo "Python 3 or standalone macOS binary not found."
    read -p "Press Enter to close..."
fi
