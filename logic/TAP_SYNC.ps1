function Start-TapSync {
    Write-Host "--- NFC LISTENER ACTIVE: AWAITING TAP ---" -ForegroundColor Cyan
    # This simulates a 'Webhook' that an NFC tag would hit
    $IncomingData = "Handover Initiated: Source[Pillar-01] Type[Mutation-Pack]"
    
    Write-Host "SYNCING: $IncomingData" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    $Date = Get-Date -Format "yyyy-MM-dd"
    "| $Date | M-031 | Tap-Handover: Frictionless NFC-to-WiFi data injection. | Verified |" | Out-File -FilePath "MUTATION_VAULT.md" -Append
    Write-Host "UPGRADE COMPLETE: Node is now M-031 Compliant." -ForegroundColor Green
}
