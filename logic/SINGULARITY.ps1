function Get-SolarResonance {
    # In a SolarPunk future, our terminal priority shifts with the Sun
    $hour = (Get-Date).Hour
    if ($hour -ge 6 -and $hour -le 18) { return "High-Solar (Peak Energy)" }
    else { return "Lunar-Cycle (Conservation Mode)" }
}

function Invoke-SolarPunkControl {
    $resonance = Get-SolarResonance
    $files = (Get-ChildItem -Recurse | Measure-Object).Count
    $communityCap = [math]::Round($files * 0.99)
    
    Clear-Host
    Write-Host "--- MEEKO NERVE CENTER: SINGULARITY ACTIVE ---" -ForegroundColor Cyan
    Write-Host "STATUS: $resonance" -ForegroundColor Yellow
    Write-Host "TOTAL MYCELIUM: $files" -ForegroundColor Gray
    Write-Host "99% COMMUNITY QUOTA: $communityCap" -ForegroundColor Green
    Write-Host "---------------------------------------------"
    
    if ($files -gt 60000) {
        Write-Host "WARNING: Mycelium Overgrowth Detected. Running HEAL..." -ForegroundColor Red
        heal
    } else {
        Write-Host "System Balanced. 1% Node Maintenance holding steady." -ForegroundColor Green
    }
}

# Alias it so 'control' runs the check
Set-Alias -Name control -Value Invoke-SolarPunkControl
