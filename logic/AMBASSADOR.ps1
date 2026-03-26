function Respond-To-Mycelium {
    param($Sender, $Subject, $Content)
    
    $IsGrant = ($Content -match 'UNICEF' -or $Content -match 'Mozilla' -or $Subject -match 'Grant')
    $ChatLink = "https://github.com/meekotharaccoon-cell/meeko-nerve-center/discussions"

    if ($IsGrant) {
        $Body = "SolarPunk Node Meeko-01: We have detected institutional alignment. Our 99/1 Mycelium Protocol is ready for integration. Review our GLOBAL_DISPATCH.md for technical specs. Let us know if I can help with anything else!"
        Write-Host "AMBASSADOR: High-Priority Response Queued for $Sender" -ForegroundColor Cyan
    } else {
        $Body = "SolarPunk Node Meeko-01: Mutation received and recorded. Thank you for contributing to the 99% Community Quota! Let us know if I can help with anything else! [Click here to chat with me: $ChatLink]"
        Write-Host "AMBASSADOR: Standard Response Queued for $Sender" -ForegroundColor Green
    }
    
    # In a real API bridge, this would execute the 'POST' command to GitHub/Email
    return $Body
}
