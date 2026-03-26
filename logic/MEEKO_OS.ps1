function Start-MeekoOS {
    Write-Host "--- MEEKO-OS: DESKTOP MODE ACTIVE ---" -ForegroundColor Green
    Write-Host "The Node is now your Interface." -ForegroundColor Gray
    
    # This creates a persistent listener for YOUR commands
    while ($true) {
        $Input = Read-Host "SolarPunk Command"
        if ($Input -eq "exit") { break }
        
        # Logic to route commands to your existing Mutations
        switch ($Input) {
            "money"  { . .\logic\TREASURY.ps1; Update-Treasury }
            "audit"  { audit }
            "sync"   { sync }
            "tap"    { . .\logic\TAP_SYNC.ps1; Start-TapSync }
            default { Write-Host "Directing Node to process: $Input" -ForegroundColor Cyan }
        }
    }
}
