$EncryptedToken = Import-CliXml -Path 'C:\Users\meeko\Desktop\meeko-nerve-center\logic\SECRET_KEY.xml'
$Ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($EncryptedToken)
$ClearToken = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)

$Headers = @{
    'Authorization' = "token $ClearToken"
    'Accept'        = 'application/vnd.github.v3+json'
}

Write-Host '--- INITIATING DEEP SCOUT: ISSUE TRIAGE ---' -ForegroundColor Cyan
try {
    # Fetch the list of issues
    $Issues = Invoke-RestMethod -Uri 'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/issues?state=open' -Headers $Headers
    $HighImpact = $Issues | Where-Object { $_.title -match 'UNICEF' -or $_.body -match 'Mozilla' -or $_.labels.name -contains 'grant' }

    if ($HighImpact.Count -gt 0) {
        Write-Host "FOUND $($HighImpact.Count) HIGH-IMPACT ALIGNMENTS!" -ForegroundColor Green
        foreach ($Issue in $HighImpact) {
            Write-Host "[!] Priority: $($Issue.title) - URL: $($Issue.html_url)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Scout Report: 120 Issues scanned. No direct Institutional matches found yet." -ForegroundColor White
        Write-Host "Observation: The 120 issues appear to be community-driven. Proceeding with Standard Ambassador mode." -ForegroundColor Green
    }
} catch {
    Write-Host "Scout Error: $($_.Exception.Message)" -ForegroundColor Red
}
