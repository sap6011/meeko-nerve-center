# SET_PAT.ps1
# Run this ONCE after creating a GitHub Personal Access Token.
# It saves the token as a user environment variable and updates the git remote.
#
# How to get a PAT:
#   1. GitHub.com → Settings → Developer Settings → Personal Access Tokens → Fine-grained
#   2. Permissions: Contents (read/write), Workflows (read/write)
#   3. Copy the token (starts with github_pat_ or ghp_)
#   4. Run: .\logic\SET_PAT.ps1 -Token "ghp_yourtoken"

param(
    [Parameter(Mandatory=$false)]
    [string]$Token,
    [string]$RepoOwner = "meekotharaccoon-cell",
    [string]$RepoName  = "meeko-nerve-center"
)

# If no token passed, prompt securely
if (-not $Token) {
    $secure = Read-Host "Paste your GitHub PAT" -AsSecureString
    $Token  = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
}

if (-not $Token -or $Token.Length -lt 10) {
    Write-Host "[XX] No token provided. Exiting." -ForegroundColor Red
    exit 1
}

# ── 1. Save as user environment variable ─────────────────────────────────
[Environment]::SetEnvironmentVariable("GITHUB_PAT", $Token, "User")
$env:GITHUB_PAT = $Token
Write-Host "[OK] GITHUB_PAT saved to user environment variables" -ForegroundColor Green

# ── 2. Update git remote URL in all repo locations ───────────────────────
$repoPaths = @(
    "$env:USERPROFILE\meeko-nerve-center",
    "C:\Users\meeko\Desktop\meeko-nerve-center\meeko-nerve-center\.claude\worktrees\agitated-tharp"
)

$newUrl = "https://$Token@github.com/$RepoOwner/$RepoName.git"

foreach ($path in $repoPaths) {
    if (Test-Path "$path\.git") {
        Push-Location $path
        git remote set-url origin $newUrl 2>&1 | Out-Null
        $current = git remote get-url origin 2>&1
        if ($current -like "*$RepoOwner*") {
            Write-Host "[OK] Remote updated: $path" -ForegroundColor Green
        } else {
            Write-Host "[!!] Failed to update remote at: $path" -ForegroundColor Yellow
        }
        Pop-Location
    }
}

# ── 3. Verify it works ───────────────────────────────────────────────────
Write-Host ""
Write-Host "Testing GitHub connection..." -ForegroundColor Cyan
$testResult = Invoke-WebRequest `
    -Uri "https://api.github.com/repos/$RepoOwner/$RepoName" `
    -Headers @{ Authorization = "token $Token" } `
    -UseBasicParsing `
    -ErrorAction SilentlyContinue

if ($testResult.StatusCode -eq 200) {
    $repo = $testResult.Content | ConvertFrom-Json
    Write-Host "[OK] GitHub connected: $($repo.full_name) ($($repo.stargazers_count) stars)" -ForegroundColor Green
} else {
    Write-Host "[!!] GitHub test failed (status $($testResult.StatusCode)) — check token permissions" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "PAT setup complete. You will not need to do this again." -ForegroundColor Green
Write-Host "Token is stored in user environment — never in the repo." -ForegroundColor Cyan
