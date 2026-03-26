Write-Host "??? [GUARD] Protective Mycelium active. Monitoring Nerve Center..." -ForegroundColor Yellow

while($true) {
    # Check if the Heartbeat task is still registered
    $task = Get-ScheduledTask -TaskName "SolarPunk_Agency_Heartbeat" -ErrorAction SilentlyContinue
    if (!$task) {
        Write-Host "?? [ALERT] Heartbeat missing! Re-manifesting..." -ForegroundColor Red
        # Trigger your registration logic here
    }
    
    # Check for unauthorized changes to the Manifesto
    if (!(Test-Path "C:\Solarpunk-Prime\docs\MANIFESTO.md")) {
        Write-Host "?? [ALERT] Manifesto compromised! Restoring from Mirror Node..." -ForegroundColor Red
        git checkout -- C:\Solarpunk-Prime\docs\MANIFESTO.md
    }

    Start-Sleep -Seconds 300 # Watch every 5 minutes
}
