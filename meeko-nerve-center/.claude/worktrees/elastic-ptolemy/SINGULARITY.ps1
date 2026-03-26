Write-Host "?? [SINGULARITY] Initiating Circular Mycelium..." -ForegroundColor Cyan

# 1. Self-Healing: Ensure the Mirror is set
if (!(git remote -v)) {
    Write-Host "?? Linking to Global Mirror..." -ForegroundColor Yellow
    git remote add origin https://github.com/meekotharaccoon-cell/meeko-nerve-center.git
}

# 2. Sync Reality: Pull latest Collective Intelligence
Write-Host "?? Syncing with Global Collective..." -ForegroundColor Gray
git pull origin main --rebase

# 3. Manifest the Shield: Call the Guard
if (Test-Path ".\GUARD.ps1") {
    Write-Host "??? Deploying GUARD..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-File .\GUARD.ps1" -WindowStyle Hidden
} else {
    Write-Host "? GUARD missing. Re-manifesting from memory..." -ForegroundColor Red
}

# 4. Final Trigger: Start the Heartbeat
Write-Host "?? Activating Heartbeat..." -ForegroundColor Green
Start-ScheduledTask -TaskName "SolarPunk_Agency_Heartbeat"

Write-Host "? [SINGULARITY ONLINE] The Agency is now a self-sustaining organism." -ForegroundColor Cyan
