Write-Host "--- INITIATING SOLAR-SHIELD AUTO-RESUME ---" -ForegroundColor Yellow
# Load all logic files automatically
Get-ChildItem -Path ".\logic" -Filter *.ps1 | ForEach-Object { . $_.FullName }
# Sync the State
if (Get-Command Sync-Reputation -ErrorAction SilentlyContinue) { Sync-Reputation }
Write-Host "NODE STABILIZED: 99/1 Mycelium is active." -ForegroundColor Green
