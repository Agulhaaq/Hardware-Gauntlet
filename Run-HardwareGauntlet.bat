@echo off
title Hardware Gauntlet Launcher
cd /d "%~dp0"

:menu
cls
echo ==========================================================
echo               HARDWARE GAUNTLET
echo    Universal Cross-Platform Hardware Diagnostic Suite
echo ==========================================================
echo.
echo Choose how you want to run Hardware Gauntlet:
echo.
echo   [1] Run Hardware Gauntlet Desktop GUI (Single Instance)
echo   [2] Run CLI Hardware Scan in this Terminal
echo   [3] Exit
echo.
set /p choice="Enter choice [1-3] (Default: 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" goto run_single_instance
if "%choice%"=="2" goto run_cli
if "%choice%"=="3" goto exit

echo Invalid choice, please select 1, 2, or 3.
pause
goto menu

:run_single_instance
echo.
echo [*] Launching Hardware Gauntlet (Single Instance)...
if exist "%~dp0HardwareGauntlet.exe" (
    start "" "%~dp0HardwareGauntlet.exe"
    exit
)
start "" pythonw -m hwscan.gui
exit

:run_cli
echo.
echo [*] Running Hardware Diagnostic Engine...
echo.
if exist "%~dp0dist\hwscan-windows-x64.exe" (
    "%~dp0dist\hwscan-windows-x64.exe"
) else (
    python -m hwscan
)
echo.
pause
goto menu

:exit
exit /b 0
