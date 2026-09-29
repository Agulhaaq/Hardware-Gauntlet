@echo off
title Hardware Gauntlet Setup
cd /d "%~dp0"

echo ==========================================================
echo        HARDWARE GAUNTLET - WINDOWS APPLICATION SETUP
echo ==========================================================
echo.
echo Installing Hardware Gauntlet to your computer...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install-windows.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred during installation.
    pause
)
