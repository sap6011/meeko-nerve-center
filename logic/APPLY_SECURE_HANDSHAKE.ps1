# APPLY_SECURE_HANDSHAKE.ps1
# Run this once as Administrator to upgrade the scheduled task
# from "blindly run anything from GitHub" to "verify GPG first"
#
# Usage (from admin PowerShell, in the repo directory):
#   .\logic\APPLY_SECURE_HANDSHAKE.ps1

# Self-elevate if not admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]"Administrator")) {
    Write-Host "Elevating to Administrator..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$repoPath     = "C:\Users\meeko\Desktop\meeko-nerve-center\meeko-nerve-center\.claude\worktrees\agitated-tharp"
$taskName     = "SolarPunk-AutoConnect"
$newScript    = "$repoPath\SECURE_HANDSHAKE.ps1"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  APPLYING SECURE HANDSHAKE PROTOCOL (M-14000)  " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# -- Remove old insecure task ---------------------------------------------
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "[OK] Removed old insecure task (blind iex execution)" -ForegroundColor Green
}

# -- Register new verified task -------------------------------------------
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File `"$newScript`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -RunLevel Highest `
    -LogonType Interactive

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "SolarPunk GPG-verified auto-connect (M-14000)" `
    -Force | Out-Null

# -- Verify ---------------------------------------------------------------
$check = (Get-ScheduledTask -TaskName $taskName | Select-Object -ExpandProperty Actions).Arguments
if ($check -like "*SECURE_HANDSHAKE*") {
    Write-Host "[OK] Task upgraded to SECURE_HANDSHAKE.ps1" -ForegroundColor Green
    Write-Host "     Old: iex(irm) blind execution" -ForegroundColor DarkGray
    Write-Host "     New: GPG verify -> execute OR Kaleidoscope trap" -ForegroundColor Green
} else {
    Write-Host "[!!] Check task manually - current args: $check" -ForegroundColor Yellow
}

Write-Host ""

# -- Sign MASTER_CONNECT.ps1 now ------------------------------------------
$gpgExe       = "C:\Program Files\GnuPG\bin\gpg.exe"
$sigKey       = "714D57142A16B477"
$masterScript = "$repoPath\meeko-nerve-center\MASTER_CONNECT.ps1"
$masterSig    = "$repoPath\MASTER_CONNECT.ps1.sig"

if ((Test-Path $gpgExe) -and (Test-Path $masterScript)) {
    & $gpgExe --detach-sign --armor --default-key $sigKey --output $masterSig $masterScript 2>&1 | Out-Null
    if (Test-Path $masterSig) {
        Write-Host "[OK] MASTER_CONNECT.ps1 signed -> MASTER_CONNECT.ps1.sig" -ForegroundColor Green
        Write-Host "     Commit .sig file to GitHub to enable full verification" -ForegroundColor Cyan
    } else {
        Write-Host "[!!] Signing failed. Run manually:" -ForegroundColor Yellow
        Write-Host "     gpg --detach-sign --armor --default-key $sigKey MASTER_CONNECT.ps1" -ForegroundColor Gray
    }
} else {
    Write-Host "[--] GPG or MASTER_CONNECT.ps1 not found - skipping auto-sign" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  SECURE HANDSHAKE ACTIVE                       " -ForegroundColor Green
Write-Host "  This machine runs only what Meeko has signed. " -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
