<#
.SYNOPSIS
    Hardware Gauntlet - Automated Windows Installer & Runner
.DESCRIPTION
    Quick 1-liner runner:
    irm https://raw.githubusercontent.com/username/Hardware-Gauntlet/main/distribution/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       ⚡ HARDWARE GAUNTLET - WINDOWS INSTALLER ⚡       " -ForegroundColor BrightCyan
Write-Host "==========================================================" -ForegroundColor Cyan

$InstallDir = "$env:LOCALAPPDATA\HardwareGauntlet"
$BinPath = "$InstallDir\hwscan.exe"
$RepoUrl = "https://github.com/Agulhaaq/Hardware-Gauntlet"

# 1. Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[✓] Python detected. Checking dependencies..." -ForegroundColor Green
    try {
        & python -m pip install psutil rich --quiet
        Write-Host "[✓] Launching Hardware Gauntlet..." -ForegroundColor Green
        
        # If repository files exist locally, run them
        if (Test-Path "hwscan\__main__.py") {
            & python -m hwscan @args
            exit 0
        }
        
        # Or install directly from GitHub / git
        & python -m pip install "git+$RepoUrl.git" --quiet
        & hwscan @args
        exit 0
    } catch {
        Write-Host "[-] Python package install encountered an error. Falling back to binary/native mode." -ForegroundColor Yellow
    }
}

# 2. Try to download standalone binary from GitHub Releases
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$ReleaseUrl = "$RepoUrl/releases/latest/download/hwscan-windows-x64.exe"
Write-Host "[*] Attempting to download standalone binary from GitHub Releases..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $ReleaseUrl -OutFile $BinPath -UseBasicParsing -TimeoutSec 15
    Write-Host "[✓] Downloaded standalone binary to $BinPath" -ForegroundColor Green
    
    # Add to User PATH if not already present
    $UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if ($UserPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", [EnvironmentVariableTarget]::User)
        Write-Host "[✓] Added $InstallDir to user PATH." -ForegroundColor Green
    }

    & $BinPath @args
    exit 0
} catch {
    Write-Host "[-] Standalone release not yet published online. Running built-in native hardware audit..." -ForegroundColor Yellow
}

# 3. Fallback: Ultra-fast native PowerShell hardware report
Write-Host "`n--- Native Windows Hardware Summary ---" -ForegroundColor BrightCyan
Get-CimInstance Win32_Processor | Select-Object -Property Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List
Get-CimInstance Win32_BaseBoard | Select-Object -Property Manufacturer, Product, SerialNumber | Format-List
Get-CimInstance Win32_PhysicalMemory | Select-Object -Property Manufacturer, Capacity, Speed, PartNumber | Format-List
Get-CimInstance Win32_VideoController | Select-Object -Property Name, DriverVersion | Format-List
Get-CimInstance Win32_DiskDrive | Select-Object -Property Model, Size, MediaType | Format-List
Write-Host "---------------------------------------" -ForegroundColor BrightCyan
