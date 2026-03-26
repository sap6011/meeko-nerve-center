function Test-Recipient {
    param($Email)
    if ($Email -match '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') {
        Write-Host "VALID: $Email is reachable. Proceeding with Handshake." -ForegroundColor Green
        return $true
    } else {
        Write-Host "ERROR: $Email is a Ghost. Aborting to prevent Loop-Back." -ForegroundColor Red
        return $false
    }
}
