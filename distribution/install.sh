#!/usr/bin/env bash
# Hardware Gauntlet - Automated Linux & macOS Installer & Runner
# Usage: curl -fsSL https://raw.githubusercontent.com/username/Hardware-Gauntlet/main/distribution/install.sh | bash

set -e

echo "=========================================================="
echo "        ⚡ HARDWARE GAUNTLET - UNIX INSTALLER ⚡          "
echo "=========================================================="

OS="$(uname -s)"
ARCH="$(uname -m)"
INSTALL_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/agulh/Hardware-Gauntlet"

mkdir -p "$INSTALL_DIR"

# 1. Try Python 3 virtual environment or pip
if command -v python3 >/dev/null 2>&1; then
    echo "[✓] Python 3 detected ($ARCH)."
    ENV_DIR="$HOME/.local/share/hardware-gauntlet/venv"
    mkdir -p "$(dirname "$ENV_DIR")"

    if [ ! -d "$ENV_DIR" ]; then
        echo "[*] Creating dedicated virtual environment..."
        python3 -m venv "$ENV_DIR" 2>/dev/null || true
    fi

    if [ -f "$ENV_DIR/bin/pip" ]; then
        echo "[*] Installing dependencies into virtual environment..."
        "$ENV_DIR/bin/pip" install psutil rich --quiet
        
        # Create wrapper in ~/.local/bin
        cat << 'EOF' > "$INSTALL_DIR/hwscan"
#!/usr/bin/env bash
VENV_PYTHON="$HOME/.local/share/hardware-gauntlet/venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    exec "$VENV_PYTHON" -m hwscan "$@"
else
    exec python3 -m hwscan "$@"
fi
EOF
        chmod +x "$INSTALL_DIR/hwscan"
        echo "[✓] Installed hwscan to $INSTALL_DIR/hwscan"
        
        # If in repository directory, install package editable
        if [ -f "pyproject.toml" ]; then
            "$ENV_DIR/bin/pip" install -e . --quiet
        fi
        
        "$INSTALL_DIR/hwscan" "$@"
        exit 0
    fi
fi

# 2. Try Pre-compiled Binary from GitHub Releases
echo "[*] Attempting to download standalone compiled binary..."
BIN_TARGET=""

if [ "$OS" = "Darwin" ]; then
    BIN_TARGET="hwscan-macos-universal"
elif [ "$OS" = "Linux" ]; then
    if [ "$ARCH" = "x86_64" ]; then
        BIN_TARGET="hwscan-linux-x64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        BIN_TARGET="hwscan-linux-arm64"
    fi
fi

if [ -n "$BIN_TARGET" ]; then
    DOWNLOAD_URL="$REPO_URL/releases/latest/download/$BIN_TARGET"
    if curl -fsSL "$DOWNLOAD_URL" -o "$INSTALL_DIR/hwscan" 2>/dev/null; then
        chmod +x "$INSTALL_DIR/hwscan"
        echo "[✓] Downloaded standalone binary to $INSTALL_DIR/hwscan"
        "$INSTALL_DIR/hwscan" "$@"
        exit 0
    fi
fi

# 3. Native Fallback
echo "[-] Running native system hardware fallback audit..."
echo "--- System & CPU ---"
uname -a
if command -v lscpu >/dev/null 2>&1; then
    lscpu
elif command -v sysctl >/dev/null 2>&1; then
    sysctl -n machdep.cpu.brand_string 2>/dev/null || true
fi

echo "--- Memory ---"
if command -v free >/dev/null 2>&1; then
    free -h
elif command -v vm_stat >/dev/null 2>&1; then
    vm_stat
fi

echo "--- Storage ---"
if command -v lsblk >/dev/null 2>&1; then
    lsblk
elif command -v df >/dev/null 2>&1; then
    df -h
fi
