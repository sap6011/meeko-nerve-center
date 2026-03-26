Write-Host "--- INITIALIZING MEEKO NERVE CENTER AUTO-SYNC ---" -ForegroundColor Yellow

# A. Load the DNA
. logic/SINGULARITY.ps1
. logic/GUARD.ps1

# B. Environmental Awareness
control

# C. The Global Sync (Connect to everything else)
Write-Host "Connecting to Global Mycelium (GitHub)..." -ForegroundColor Cyan
git push origin main --force

# D. Final Pulse of the Cycle
pulse

Write-Host "--- NODE SYNC COMPLETE. SYSTEM BREATHING. ---" -ForegroundColor Green

. .\logic\MORNING_BRIEF.ps1
