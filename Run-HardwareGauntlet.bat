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
echo   [1] Just Run (One-Off Portable Instance - No Installation)
echo   [2] Install as Full Application (Desktop, Start Menu, Apps)
echo   [3] Run CLI Hardware Scan in this Terminal
echo   [4] Exit
echo.
set /p choice="Enter choice [1-4] (Default: 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" goto run_portable
if "%choice%"=="2" goto install_app
if "%choice%"=="3" goto run_cli
if "%choice%"=="4" goto exit

echo Invalid choice, please select 1, 2, 3, or 4.
pause
goto menu

:run_portable
echo.
echo [*] Launching Hardware Gauntlet Portable...
if exist "%~dp0HardwareGauntlet.exe" (
    start "" "%~dp0HardwareGauntlet.exe"
    exit
)
start "" pythonw -m hwscan.gui
exit

:install_app
echo.
echo [*] Launching Hardware Gauntlet Installer...
if exist "%~dp0Setup-HardwareGauntlet.exe" (
    start "" "%~dp0Setup-HardwareGauntlet.exe"
    exit
)
call "%~dp0Install-HardwareGauntlet.bat"
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
echo Press any key to return to menu...
pause >nul
goto menu

:exit
exit
