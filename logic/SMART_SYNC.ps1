function sync {
    Write-Host "--- INITIATING SMART-SYNC (M-032.1) ---" -ForegroundColor Cyan
    
    # Step 1: Pack everything local first (The 'Safe' move)
    git add .
    $Message = "Solar-Sync: 2026-03-23 00:01"
    git commit -m "$Message"
    
    # Step 2: Listen for Cloud Updates (The 'Realign' move)
    Write-Host "Realigning with the Mycelium..." -ForegroundColor Gray
    git pull origin main --rebase
    
    # Step 3: Talk (The 'Push' move)
    Write-Host "Pushing 32 Mutations to the Cloud..." -ForegroundColor Gray
    git push origin main
    
    Write-Host "--- NODE SYNC COMPLETE ---" -ForegroundColor Green
}
