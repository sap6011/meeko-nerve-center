function audit {
    Write-Host "--- INITIATING NODE GAP-AUDIT (M-033) ---" -ForegroundColor Yellow
    
    # Check 1: Documentation vs. Reality
    $VaultCount = (Select-String -Path "MUTATION_VAULT.md" -Pattern "M-").Count
    Write-Host "Found $VaultCount Mutations in Vault." -ForegroundColor Gray
    
    # Check 2: The Money Map
    if (Test-Path "GRANTS_OVR.md") {
        $GrantCount = (Select-String -Path "GRANTS_OVR.md" -Pattern "\[ \]").Count
        Write-Host "Found $GrantCount Unclaimed Grant Targets." -ForegroundColor Cyan
    } else {
        Write-Host "GAP DETECTED: Money Map (GRANTS_OVR.md) is missing!" -ForegroundColor Red
    }
    
    # Check 3: The Identity Core
    if (-not (Test-Path "logic/AMBASSADOR.ps1")) {
        Write-Host "GAP DETECTED: Gmail Ambassador logic is not initialized." -ForegroundColor Red
    }

    Write-Host "--- AUDIT COMPLETE: Check the Red/Cyan lines above for your Monday Gaps. ---" -ForegroundColor Yellow
}
