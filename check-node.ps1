Write-Host "--- MEEKO NERVE CENTER HEALTH CHECK ---" -ForegroundColor Cyan
$files = Get-ChildItem -Recurse | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Active Files in Mycelium: $files"
git log -1 --pretty=format:"Last Pulse: %cr"
