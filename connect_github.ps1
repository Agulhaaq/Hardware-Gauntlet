<#
.SYNOPSIS
    Connect and Push Hardware Gauntlet to GitHub
.DESCRIPTION
    Automates creating the GitHub repository and pushing the codebase.
#>

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$gitPath = "C:\Program Files\Git\cmd\git.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     ⚡ HARDWARE GAUNTLET - GITHUB REPOSITORY SYNC ⚡    " -ForegroundColor BrightCyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check GitHub CLI login status
& $ghPath auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] You are not currently logged into GitHub CLI." -ForegroundColor Yellow
    Write-Host "[*] Launching GitHub browser login..." -ForegroundColor Cyan
    & $ghPath auth login --web -h github.com -p https
}

# Prompt or create repo
Write-Host "`n[*] Creating GitHub repository and pushing codebase..." -ForegroundColor Cyan
& $ghPath repo create Hardware-Gauntlet --public --source=. --remote=origin --push

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[✓] Repository successfully created and pushed to GitHub!" -ForegroundColor Green
    & $ghPath browse
} else {
    Write-Host "`n[-] If the repository already exists on GitHub, link it with:" -ForegroundColor Yellow
    Write-Host "    git remote add origin https://github.com/<your-username>/<repo-name>.git" -ForegroundColor Cyan
    Write-Host "    git push -u origin main" -ForegroundColor Cyan
}
