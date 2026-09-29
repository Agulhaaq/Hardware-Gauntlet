#!/usr/bin/env bash
# Hardware Gauntlet - Native macOS Application Installer
# Copies Hardware Gauntlet.app to /Applications and adds command-line links.

set -e

echo "=========================================================="
echo "    ⚡ HARDWARE GAUNTLET - NATIVE MACOS INSTALLER ⚡     "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_APP="/Applications/Hardware Gauntlet.app"
BIN_DIR="/usr/local/bin"

echo "[1/3] Installing Hardware Gauntlet to /Applications..."
rm -rf "$TARGET_APP"
cp -R "$SCRIPT_DIR/Hardware Gauntlet.app" "$TARGET_APP"

# Copy python package into app bundle
mkdir -p "$TARGET_APP/Contents/Resources"
cp -r "$SCRIPT_DIR/hwscan" "$TARGET_APP/Contents/Resources/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/assets" "$TARGET_APP/Contents/Resources/" 2>/dev/null || true

# If standalone macos binary is compiled, include it
if [ -f "$SCRIPT_DIR/dist/hwscan-macos-universal" ]; then
    cp "$SCRIPT_DIR/dist/hwscan-macos-universal" "$TARGET_APP/Contents/MacOS/hwscan-bin"
    chmod +x "$TARGET_APP/Contents/MacOS/hwscan-bin"
fi

chmod +x "$TARGET_APP/Contents/MacOS/HardwareGauntlet"

echo "[2/3] Registering command-line tool..."
if [ -d "$BIN_DIR" ] && [ -w "$BIN_DIR" ]; then
    ln -sf "$TARGET_APP/Contents/MacOS/HardwareGauntlet" "$BIN_DIR/hwscan"
    ln -sf "$TARGET_APP/Contents/MacOS/HardwareGauntlet" "$BIN_DIR/hardware-gauntlet"
fi

echo "[3/3] Refreshing Launchpad and Spotlight..."
touch "$TARGET_APP"

echo "=========================================================="
echo "   [✓] HARDWARE GAUNTLET SUCCESSFULLY INSTALLED!         "
echo "=========================================================="
echo "• Open from: Spotlight (Cmd + Space -> 'Hardware Gauntlet')"
echo "• Open from: Finder -> Applications -> Hardware Gauntlet"
echo "• Open from: Terminal -> 'hwscan'"
