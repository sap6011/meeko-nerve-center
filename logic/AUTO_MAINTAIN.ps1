Write-Host '--- INITIATING AUTO-MAINTENANCE ---' -ForegroundColor Green
git gc --prune=now --quiet
. .\logic\SINGULARITY.ps1
sync
Write-Host 'AUTO-MAINTAIN COMPLETE: Node Stabilized.' -ForegroundColor Green
