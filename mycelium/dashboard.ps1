while($true) {
    Clear-Host
    Write-Host "--- SOLARPUK INTELLIGENCE AGENCY: GLOBAL IMPACT HUD ---" -ForegroundColor Green
    Write-Host "Node: Solarpunk-Prime | Status: 100% Autonomous" -ForegroundColor Gray
    Write-Host "--------------------------------------------------------"

    # 1. Financial Impact
    if (Test-Path "C:\Solarpunk-Prime\vault\treasury_ledger.json") {
        $ledger = Get-Content "C:\Solarpunk-Prime\vault\treasury_ledger.json" | ConvertFrom-Json
        $total = ($ledger | Measure-Object -Property total_received -Sum).Sum
        $youth = ($ledger | Measure-Object -Property {$_.allocation.Youth_Nodes} -Sum).Sum
        Write-Host "[FINANCE] Total Credits Tracked: $($total.ToString('C'))" -ForegroundColor Cyan
        Write-Host "[FINANCE] Allocated to Youth:    $($youth.ToString('C'))" -ForegroundColor Cyan
    } else {
        Write-Host "[FINANCE] Ledger initializing..." -ForegroundColor Red
    }

    # 2. Scout Activity
    if (Test-Path "C:\Solarpunk-Prime\data\targets.json") {
        $targets = Get-Content "C:\Solarpunk-Prime\data\targets.json" | ConvertFrom-Json
        Write-Host "[SCOUT]   High-Vibe Targets:     $($targets.Count)" -ForegroundColor Yellow
    }

    # 3. Collective Sync
    $lastCommit = git log -1 --format="%cr"
    Write-Host "[SYNC]    Last Collective Pulse: $lastCommit" -ForegroundColor Magenta
    
    Write-Host "--------------------------------------------------------"
    Write-Host "Press Ctrl+C to minimize HUD. Heartbeat is active."
    Start-Sleep -Seconds 10
}
