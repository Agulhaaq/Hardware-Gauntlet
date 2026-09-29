<#
.SYNOPSIS
    Hardware Gauntlet Windows System Installer
.DESCRIPTION
    Installs Hardware Gauntlet as a permanent native desktop application:
    - Installs to %LOCALAPPDATA%\Programs\HardwareGauntlet
    - Creates Start Menu shortcut (searchable in Windows Search)
    - Creates Desktop shortcut
    - Adds to User PATH
    - Registers in Windows Settings > Apps > Installed apps
#>

param(
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$SourceDir = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$SourceDir\HardwareGauntlet.exe")) {
    $SourceDir = $PSScriptRoot
}

$InstallDir = "$env:LOCALAPPDATA\Programs\HardwareGauntlet"
$AssetsDir = "$InstallDir\assets"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    [*] HARDWARE GAUNTLET - NATIVE WINDOWS INSTALLER [*]   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Create installation directories
Write-Host "[1/5] Creating application folder at $InstallDir..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $AssetsDir -Force | Out-Null

# 2. Copy binaries and assets
Write-Host "[2/5] Copying program files and assets..." -ForegroundColor Cyan
if (Test-Path "$SourceDir\HardwareGauntlet.exe") {
    Copy-Item "$SourceDir\HardwareGauntlet.exe" "$InstallDir\HardwareGauntlet.exe" -Force
}
if (Test-Path "$SourceDir\dist\hwscan-windows-x64.exe") {
    Copy-Item "$SourceDir\dist\hwscan-windows-x64.exe" "$InstallDir\hwscan.exe" -Force
} elseif (Test-Path "$SourceDir\hwscan-windows-x64.exe") {
    Copy-Item "$SourceDir\hwscan-windows-x64.exe" "$InstallDir\hwscan.exe" -Force
}

# Copy icons and uninstaller
if (Test-Path "$SourceDir\assets\app.ico") {
    Copy-Item "$SourceDir\assets\app.ico" "$AssetsDir\app.ico" -Force
}
if (Test-Path "$SourceDir\assets\app.png") {
    Copy-Item "$SourceDir\assets\app.png" "$AssetsDir\app.png" -Force
}
if (Test-Path "$PSScriptRoot\uninstall-windows.ps1") {
    Copy-Item "$PSScriptRoot\uninstall-windows.ps1" "$InstallDir\uninstall.ps1" -Force
}

# 3. Create Windows Shortcuts
Write-Host "[3/5] Creating Start Menu and Desktop shortcuts..." -ForegroundColor Cyan
$WshShell = New-Object -ComObject WScript.Shell

$TargetExe = "$InstallDir\HardwareGauntlet.exe"
$IconFile = "$AssetsDir\app.ico"

# Start Menu Shortcut
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Hardware Gauntlet.lnk"
$StartShortcut = $WshShell.CreateShortcut($StartMenuPath)
$StartShortcut.TargetPath = $TargetExe
$StartShortcut.WorkingDirectory = $InstallDir
$StartShortcut.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
if (Test-Path $IconFile) { $StartShortcut.IconLocation = "$IconFile,0" }
$StartShortcut.Save()

# Desktop Shortcut
$DesktopPath = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Hardware Gauntlet.lnk")
$DesktopShortcut = $WshShell.CreateShortcut($DesktopPath)
$DesktopShortcut.TargetPath = $TargetExe
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.Description = "Hardware Gauntlet - Hardware Diagnostic Suite"
if (Test-Path $IconFile) { $DesktopShortcut.IconLocation = "$IconFile,0" }
$DesktopShortcut.Save()

# 4. Register in Windows Settings > Apps > Installed apps (Control Panel Uninstall)
Write-Host "[4/5] Registering with Windows Add/Remove Programs..." -ForegroundColor Cyan
$RegKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HardwareGauntlet"
New-Item -Path $RegKey -Force | Out-Null
Set-ItemProperty -Path $RegKey -Name "DisplayName" -Value "Hardware Gauntlet"
Set-ItemProperty -Path $RegKey -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegKey -Name "Publisher" -Value "Hardware Gauntlet Team"
Set-ItemProperty -Path $RegKey -Name "InstallLocation" -Value $InstallDir
Set-ItemProperty -Path $RegKey -Name "DisplayIcon" -Value "$IconFile"
Set-ItemProperty -Path $RegKey -Name "UninstallString" -Value ('powershell.exe -ExecutionPolicy Bypass -NoProfile -File "' + $InstallDir + '\uninstall.ps1"')
Set-ItemProperty -Path $RegKey -Name "EstimatedSize" -Value 41000

# 5. Add to User PATH
Write-Host "[5/5] Adding Hardware Gauntlet to system PATH..." -ForegroundColor Cyan
$userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($userPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$InstallDir", [EnvironmentVariableTarget]::User)
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   [+] HARDWARE GAUNTLET SUCCESSFULLY INSTALLED!         " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "- Location: $InstallDir" -ForegroundColor White
Write-Host "- Desktop Shortcut: Created on Desktop" -ForegroundColor White
Write-Host "- Start Menu: Search 'Hardware Gauntlet' in Windows Search" -ForegroundColor White
Write-Host "- CLI Command: Type 'hwscan' in any PowerShell / CMD window" -ForegroundColor White

if (-not $NoLaunch) {
    Write-Host ""
    Write-Host "[*] Launching Hardware Gauntlet..." -ForegroundColor Cyan
    Start-Process $TargetExe
}
