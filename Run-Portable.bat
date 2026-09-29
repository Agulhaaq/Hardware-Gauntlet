@echo off
title Hardware Gauntlet (Portable)
cd /d "%~dp0"

echo ==========================================================
echo       HARDWARE GAUNTLET - ONE-OFF PORTABLE INSTANCE
echo ==========================================================
echo Starting Hardware Gauntlet immediately without installation...
echo.

if exist "%~dp0HardwareGauntlet.exe" (
    start "" "%~dp0HardwareGauntlet.exe"
    exit
)

if exist "%~dp0dist\hwscan-windows-x64.exe" (
    start "" "%~dp0dist\hwscan-windows-x64.exe" --gui
    exit
)

start "" pythonw -m hwscan.gui
exit
