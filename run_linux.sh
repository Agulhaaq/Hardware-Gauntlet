#!/usr/bin/env bash
# Hardware Gauntlet - Double-clickable Linux Desktop Launcher

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f "$DIR/dist/hwscan-linux-x64" ]; then
    chmod +x "$DIR/dist/hwscan-linux-x64"
    "$DIR/dist/hwscan-linux-x64" --gui
elif command -v python3 >/dev/null 2>&1; then
    python3 -m hwscan --gui
else
    echo "Python 3 or standalone Linux binary not found."
    read -p "Press Enter to exit..."
fi
