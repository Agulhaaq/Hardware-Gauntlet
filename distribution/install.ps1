<#
.SYNOPSIS
    Hardware Gauntlet - Instant Standalone Portable Runner (No Installation Required)
.DESCRIPTION
    Quick 1-liner runner:
    irm https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/distribution/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ⚡ HARDWARE GAUNTLET - PORTABLE RUNNER (NO INSTALL) ⚡ " -ForegroundColor BrightCyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. If running locally inside repo or folder with HardwareGauntlet.exe, run immediately
if (Test-Path "HardwareGauntlet.exe") {
    Write-Host "[✓] Launching standalone HardwareGauntlet.exe..." -ForegroundColor Green
    Start-Process ".\HardwareGauntlet.exe"
    exit 0
}

# 2. If Python is available, execute in-memory scan
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[✓] Python detected. Launching portable hardware scan..." -ForegroundColor Green
    try {
        if (Test-Path "hwscan\__main__.py") {
            & python -m hwscan @args
            exit 0
        }
        & python -m pip install psutil rich --quiet
        & python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/hwscan/cli.py').read().decode())" @args
        exit 0
    } catch {
        Write-Host "[-] Python execution skipped. Falling back to native Windows telemetry..." -ForegroundColor Yellow
    }
}

# 3. Native Windows Hardware Summary (Zero dependencies, Zero install)
Write-Host "`n--- Native Windows Hardware Summary ---" -ForegroundColor BrightCyan
Get-CimInstance Win32_Processor | Select-Object -Property Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List
Get-CimInstance Win32_BaseBoard | Select-Object -Property Manufacturer, Product, SerialNumber | Format-List
Get-CimInstance Win32_PhysicalMemory | Select-Object -Property Manufacturer, Capacity, Speed, PartNumber | Format-List
Get-CimInstance Win32_VideoController | Select-Object -Property Name, DriverVersion | Format-List
Get-CimInstance Win32_DiskDrive | Select-Object -Property Model, Size, MediaType | Format-List
Write-Host "---------------------------------------" -ForegroundColor BrightCyan
