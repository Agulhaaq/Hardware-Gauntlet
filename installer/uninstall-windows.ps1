<#
.SYNOPSIS
    Hardware Gauntlet Windows Uninstaller
#>

$ErrorActionPreference = "SilentlyContinue"

$InstallDir = "$env:LOCALAPPDATA\Programs\HardwareGauntlet"
$StartMenuLnk = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Hardware Gauntlet.lnk"
$DesktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Hardware Gauntlet.lnk")

Write-Host "Uninstalling Hardware Gauntlet..." -ForegroundColor Cyan

# 1. Remove Shortcuts
if (Test-Path $StartMenuLnk) { Remove-Item $StartMenuLnk -Force }
if (Test-Path $DesktopLnk) { Remove-Item $DesktopLnk -Force }

# 2. Remove Registry Entry
Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HardwareGauntlet" -Recurse -Force

# 3. Remove from PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($userPath -like "*$InstallDir*") {
    $newPath = ($userPath.Split(';') | Where-Object { $_ -ne $InstallDir -and $_ -ne "" }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::User)
}

# 4. Remove Files (schedule removal if running from install dir)
Start-Sleep -Seconds 1
Start-Process powershell.exe -ArgumentList "-NoProfile -Command `Start-Sleep -Seconds 2; Remove-Item -Path '$InstallDir' -Recurse -Force`" -WindowStyle Hidden

Write-Host "[+] Hardware Gauntlet has been completely uninstalled from your computer." -ForegroundColor Green
