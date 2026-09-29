#!/usr/bin/env bash
# Hardware Gauntlet - Native Linux Application Installer
# Installs application, desktop launcher, icons, and terminal commands.

set -e

echo "=========================================================="
echo "    ⚡ HARDWARE GAUNTLET - NATIVE LINUX INSTALLER ⚡     "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if root or user install
if [ "$(id -u)" -eq 0 ]; then
    BIN_DIR="/usr/local/bin"
    APP_DIR="/usr/local/share/hardware-gauntlet"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor/scalable/apps"
else
    BIN_DIR="$HOME/.local/bin"
    APP_DIR="$HOME/.local/share/hardware-gauntlet"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
fi

mkdir -p "$BIN_DIR" "$APP_DIR" "$DESKTOP_DIR" "$ICON_DIR"

echo "[1/4] Copying application files to $APP_DIR..."
cp -r "$SCRIPT_DIR/hwscan" "$APP_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/assets" "$APP_DIR/" 2>/dev/null || true

# Copy standalone binary if compiled
if [ -f "$SCRIPT_DIR/dist/hwscan-linux-x64" ]; then
    cp "$SCRIPT_DIR/dist/hwscan-linux-x64" "$APP_DIR/hardware-gauntlet-bin"
    chmod +x "$APP_DIR/hardware-gauntlet-bin"
fi

echo "[2/4] Installing application launchers in $BIN_DIR..."
cat << 'EOF' > "$BIN_DIR/hardware-gauntlet"
#!/usr/bin/env bash
APP_DIR_DEFAULT="/usr/local/share/hardware-gauntlet"
APP_DIR_USER="$HOME/.local/share/hardware-gauntlet"
if [ -d "$APP_DIR_USER" ]; then
    TARGET_DIR="$APP_DIR_USER"
else
    TARGET_DIR="$APP_DIR_DEFAULT"
fi

if [ -f "$TARGET_DIR/hardware-gauntlet-bin" ]; then
    exec "$TARGET_DIR/hardware-gauntlet-bin" "$@"
else
    PYTHONPATH="$TARGET_DIR:$PYTHONPATH" exec python3 -m hwscan "$@"
fi
EOF

chmod +x "$BIN_DIR/hardware-gauntlet"
ln -sf "$BIN_DIR/hardware-gauntlet" "$BIN_DIR/hwscan"

echo "[3/4] Installing desktop entry and icons..."
if [ -f "$SCRIPT_DIR/assets/app.png" ]; then
    cp "$SCRIPT_DIR/assets/app.png" "$ICON_DIR/hardware-gauntlet.png"
fi

cat << EOF > "$DESKTOP_DIR/hardware-gauntlet.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Hardware Gauntlet
GenericName=Hardware Diagnostic Suite
Comment=Universal Cross-Platform Hardware Scanner & Diagnostic Suite
Exec=$BIN_DIR/hardware-gauntlet --gui
Icon=hardware-gauntlet
Terminal=false
Categories=System;Monitor;HardwareSettings;
Keywords=hardware;diagnostic;cpu;gpu;ram;disk;scanner;
StartupNotify=true
EOF

chmod +x "$DESKTOP_DIR/hardware-gauntlet.desktop"

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo "[4/4] Creating uninstaller..."
cat << EOF > "$APP_DIR/uninstall.sh"
#!/usr/bin/env bash
rm -f "$BIN_DIR/hardware-gauntlet" "$BIN_DIR/hwscan"
rm -f "$DESKTOP_DIR/hardware-gauntlet.desktop"
rm -f "$ICON_DIR/hardware-gauntlet.png"
rm -rf "$APP_DIR"
echo "[✓] Hardware Gauntlet uninstalled."
EOF
chmod +x "$APP_DIR/uninstall.sh"

echo "=========================================================="
echo "   [✓] HARDWARE GAUNTLET SUCCESSFULLY INSTALLED!         "
echo "=========================================================="
echo "• Desktop Menu: Search for 'Hardware Gauntlet'"
echo "• CLI Commands: 'hardware-gauntlet' or 'hwscan'"
echo "• Uninstaller: $APP_DIR/uninstall.sh"
