@echo off
title Hardware Gauntlet
cd /d "%~dp0"

:: 1. Check if compiled standalone application exists in folder
if exist "%~dp0HardwareGauntlet.exe" (
    start "" "%~dp0HardwareGauntlet.exe"
    exit /b 0
)

:: 2. Otherwise run using Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw -m hwscan --gui
    exit /b 0
)

:: 3. Fallback to CLI binary if present
if exist "%~dp0dist\hwscan-windows-x64.exe" (
    start "" "%~dp0dist\hwscan-windows-x64.exe"
    exit /b 0
)

echo Python or HardwareGauntlet.exe not found in this folder.
pause
