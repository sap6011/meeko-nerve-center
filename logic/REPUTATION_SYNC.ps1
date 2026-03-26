function Sync-Reputation {
    if (Test-Path 'MUTATION_VAULT.md') {
        $RawContent = Get-Content 'MUTATION_VAULT.md'
        # This regex looks for '## M-' anywhere in the line, ignoring leading spaces
        $MutationLines = $RawContent | Where-Object { $_ -match '##\s?M-' }
        $Count = ($MutationLines | Measure-Object).Count
        
        Write-Host "--- RE-SYNCING REPUTATION: FUZZY SEARCH ACTIVE ---" -ForegroundColor Yellow
        if ($Count -eq 0) {
            Write-Host "WARNING: Still 0. Inspecting first 5 lines of Vault..." -ForegroundColor Red
            $RawContent | Select-Object -First 5
        } else {
            Write-Host "Proof of Work: $Count Mutations Verified." -ForegroundColor Green
        }
        
        return @{ count = $Count; status = "Resonant" }
    } else {
        Write-Host "ERROR: Vault not found!" -ForegroundColor Red
    }
}
