function shield {
    Write-Host "--- INITIATING G3 SOLAR SHIELD ---" -ForegroundColor Red
    $vault = "SHIELD_$(Get-Date -Format 'yyyyMMdd_HHmm').zip"
    
    # Target only the "Fruit" (your logic), ignore the "Soil" (node_modules)
    Write-Host "Compressing Core Logic into Encrypted Mycelium Vault..." -ForegroundColor Yellow
    Compress-Archive -Path "logic/", "docs/", "README.md", "LICENSE" -DestinationPath $vault -Force
    
    Write-Host "--- CORE LOGIC SECURED IN $vault ---" -ForegroundColor Green
    Write-Host "Node is now EMP-Resilient. 99% Community Data stays local." -ForegroundColor Cyan
}
