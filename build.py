"""Build script to compile standalone native executables using PyInstaller."""

import os
import sys
import shutil
import platform
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def build():
    print("=" * 60)
    print(" [*] HARDWARE GAUNTLET - STANDALONE BINARY COMPILER")
    print("=" * 60)

    current_os = platform.system().lower()
    machine = platform.machine().lower()

    if current_os == "windows":
        bin_name = "hwscan-windows-x64.exe" if "64" in machine else "hwscan-windows-x86.exe"
    elif current_os == "darwin":
        bin_name = "hwscan-macos-universal"
    else:
        bin_name = f"hwscan-linux-{machine}"

    print(f"[*] Target OS: {current_os} ({machine})")
    print(f"[*] Output Executable Name: {bin_name}")

    # Verify PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller is not installed. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    sep = ";" if current_os == "windows" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--onefile",
        "--name", os.path.splitext(bin_name)[0],
        "--hidden-import", "rich",
        "--hidden-import", "psutil",
        "--hidden-import", "hwscan",
        "--hidden-import", "PIL",
    ]

    if os.path.exists("assets"):
        cmd.extend(["--add-data", f"assets{sep}assets"])

    if current_os == "windows" and os.path.exists("assets/app.ico"):
        cmd.extend(["--icon", "assets/app.ico"])

    cmd.append("hwscan/__main__.py")

    print(f"[*] Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    dist_dir = os.path.join(os.getcwd(), "dist")
    built_file = os.path.join(dist_dir, os.path.splitext(bin_name)[0] + (".exe" if current_os == "windows" else ""))
    target_file = os.path.join(dist_dir, bin_name)

    if os.path.exists(built_file) and built_file != target_file:
        if os.path.exists(target_file):
            os.remove(target_file)
        os.rename(built_file, target_file)

    print("=" * 60)
    print(f"[✓] BUILD SUCCESSFUL! Compiled binary saved at:")
    print(f"    {target_file}")
    print("=" * 60)


if __name__ == "__main__":
    build()
