# Load the Existing Secure Key from your logic folder
$EncryptedToken = Import-CliXml -Path 'C:\Users\meeko\Desktop\meeko-nerve-center\logic\SECRET_KEY.xml'
$Ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($EncryptedToken)
$ClearToken = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)

$Headers = @{
    'Authorization' = "token $ClearToken"
    'Accept'        = 'application/vnd.github.v3+json'
}

Write-Host '--- POLLING GLOBAL MYCELIUM (GITHUB API) ---' -ForegroundColor Cyan
try {
    # Get Repo Stats (Stars, Forks, Open Issues)
    $RepoData = Invoke-RestMethod -Uri 'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center' -Headers $Headers
    Write-Host "Stars: $($RepoData.stargazers_count) | Forks: $($RepoData.forks_count) | Issues: $($RepoData.open_issues_count)" -ForegroundColor White
    
    # Get Notifications
    $Notes = Invoke-RestMethod -Uri 'https://api.github.com/notifications' -Headers $Headers
    Write-Host "New Notifications: $($Notes.Count)" -ForegroundColor Green
} catch {
    Write-Host "Error connecting to Mycelium: $($_.Exception.Message)" -ForegroundColor Red
}
