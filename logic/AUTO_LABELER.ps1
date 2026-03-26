$EncryptedToken = Import-CliXml -Path 'C:\Users\meeko\Desktop\meeko-nerve-center\logic\SECRET_KEY.xml'
$Ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($EncryptedToken)
$ClearToken = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)
$Headers = @{ 'Authorization' = "token $ClearToken"; 'Accept' = 'application/vnd.github.v3+json' }

Write-Host '--- MEEKO-01: INITIATING AUTO-LABELER ---' -ForegroundColor Cyan
try {
    $Issues = Invoke-RestMethod -Uri 'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/issues?state=open' -Headers $Headers
    foreach ($Issue in $Issues) {
        $LabelsToAdd = @()
        if ($Issue.title -match 'bug|error|fail') { $LabelsToAdd += "bug" }
        if ($Issue.title -match 'idea|feature|add') { $LabelsToAdd += "enhancement" }
        if ($Issue.body -match 'Mozilla|UNICEF|Grant') { $LabelsToAdd += "Institutional" }
        
        if ($LabelsToAdd.Count -gt 0) {
            $Body = @{ labels = $LabelsToAdd } | ConvertTo-Json
            Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/issues/$($Issue.number)/labels" -Headers $Headers -Body $Body
            Write-Host "Labeled Issue #$($Issue.number) as $($LabelsToAdd -join ', ')" -ForegroundColor Green
        }
    }
} catch { Write-Host "Labeler Error: $($_.Exception.Message)" -ForegroundColor Red }
