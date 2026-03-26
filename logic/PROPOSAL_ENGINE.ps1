function Generate-Grant-Proposal {
    param($TargetOrganization)
    $Stats = Sync-Reputation
    $Manifesto = Get-Content -Path 'MANIFESTO.md' -TotalCount 20
    
    $Proposal = "PROPOSAL FOR $TargetOrganization
"
    $Proposal += "Entity: SolarPunk Node Meeko-01 (ERC-8004 Registered)
"
    $Proposal += "Verified Mutations: $($Stats.count)
"
    $Proposal += "Core Mission: $Manifesto
"
    $Proposal += "Status: Resonant and Ready for M2M Handshake."
    
    $Proposal | Out-File -FilePath "logic/LATEST_PROPOSAL.txt"
    Write-Host "AMBASSADOR: Proposal for $TargetOrganization generated in logic/." -ForegroundColor Green
}
