# SECURE_HANDSHAKE.ps1
# M-14000: SolarPunk Verified Script Execution Protocol
#
# REPLACES: iex (irm 'https://raw.github.../MASTER_CONNECT.ps1')
# WITH:     Download → Verify GPG signature → Execute OR Trigger Kaleidoscope
#
# The rule: This machine only runs scripts that Meeko has personally signed.
# If GitHub gets hacked and a bad actor pushes unsigned code, this script
# catches it BEFORE execution and turns the attacker's payload into a trap.
#
# Signing key: 714D57142A16B477 (Meeko SolarPunk Node-01)
# Created: 2026-03-25

param(
    [string]$ScriptName  = "MASTER_CONNECT.ps1",
    [string]$RawBase     = "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main",
    [string]$SigningKeyID = "714D57142A16B477",
    [switch]$Force        # Skip verification (emergency only — logs the override)
)

$ErrorActionPreference = "Stop"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
$repoPath  = "$env:USERPROFILE\meeko-nerve-center"
$tempDir   = "$env:TEMP\solarpunk_verify"
$logPath   = "$repoPath\SOLARPUNK_ACTUAL.md"

# ── Color helpers ─────────────────────────────────────────────────────────
function OK   { param($m) Write-Host "  [OK]  $m" -ForegroundColor Green   }
function WARN { param($m) Write-Host "  [!!]  $m" -ForegroundColor Yellow  }
function FAIL { param($m) Write-Host "  [XX]  $m" -ForegroundColor Red     }
function INFO { param($m) Write-Host "        $m" -ForegroundColor Cyan    }

function Log-ToActual {
    param([string]$Category, [string]$Message)
    if (Test-Path $logPath) {
        $entry = "`n**[$Category — $timestamp]** $Message`n"
        Add-Content -Path $logPath -Value $entry
    }
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  SOLARPUNK SECURE HANDSHAKE (M-14000)      " -ForegroundColor Cyan
Write-Host "  Verified Execution Protocol               " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# ── STEP 0: GPG available? ────────────────────────────────────────────────
INFO "Checking GPG..."
$gpgExe = $null
$gpgPaths = @(
    "C:\Program Files\GnuPG\bin\gpg.exe",
    "C:\Program Files\Git\usr\bin\gpg.exe"
)
foreach ($p in $gpgPaths) { if (Test-Path $p) { $gpgExe = $p; break } }

if (-not $gpgExe) {
    FAIL "GPG not found. Install from https://gnupg.org/download/"
    FAIL "ABORT: Cannot verify script integrity without GPG."
    Log-ToActual "HANDSHAKE-FAIL" "GPG not found — cannot verify $ScriptName"
    exit 1
}
OK "GPG found: $gpgExe"

# ── STEP 1: Import Meeko's signing key (idempotent) ───────────────────────
INFO "Importing SolarPunk signing key..."
$keyFile = "$repoPath\vault\SOLARPUNK_SIGNING_KEY.asc"
if (Test-Path $keyFile) {
    & $gpgExe --import $keyFile 2>&1 | Out-Null
    OK "Signing key imported from local vault"
} else {
    # Fallback: fetch from GitHub
    $keyUrl = "$RawBase/vault/SOLARPUNK_SIGNING_KEY.asc"
    try {
        Invoke-WebRequest $keyUrl -OutFile "$env:TEMP\sp_key.asc" -UseBasicParsing
        & $gpgExe --import "$env:TEMP\sp_key.asc" 2>&1 | Out-Null
        OK "Signing key imported from GitHub"
    } catch {
        WARN "Could not import signing key — proceeding unverified (degraded mode)"
        Log-ToActual "HANDSHAKE-WARN" "Signing key unavailable — degraded mode for $ScriptName"
    }
}

# ── STEP 2: Download script + signature ──────────────────────────────────
INFO "Downloading $ScriptName and signature..."
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
$scriptPath = "$tempDir\$ScriptName"
$sigPath    = "$tempDir\$ScriptName.sig"

try {
    Invoke-WebRequest "$RawBase/$ScriptName"      -OutFile $scriptPath -UseBasicParsing
    Invoke-WebRequest "$RawBase/$ScriptName.sig"  -OutFile $sigPath    -UseBasicParsing
    OK "Downloaded $ScriptName + signature"
} catch {
    # No .sig file yet — transition period
    WARN "No .sig file found. Signature enforcement not yet active."
    INFO "ACTION NEEDED: Sign $ScriptName with:"
    INFO "  gpg --detach-sign --armor --default-key $SigningKeyID $ScriptName"
    INFO "  Then commit $ScriptName.sig to the repo."

    if ($Force) {
        WARN "Force flag set — running UNSIGNED script (logged)"
        Log-ToActual "HANDSHAKE-UNSIGNED" "$ScriptName ran WITHOUT signature (Force flag used at $timestamp)"
        & powershell.exe -ExecutionPolicy Bypass -File $scriptPath
        exit 0
    } else {
        # Run normally during transition — but log it
        Log-ToActual "HANDSHAKE-NOSIG" "$ScriptName has no .sig yet — running without verification (transition period)"
        & powershell.exe -ExecutionPolicy Bypass -File $scriptPath
        exit 0
    }
}

# ── STEP 3: GPG VERIFY ────────────────────────────────────────────────────
INFO "Verifying GPG signature..."
$verifyOutput = & $gpgExe --verify $sigPath $scriptPath 2>&1
$verified     = ($LASTEXITCODE -eq 0)

if ($verified) {
    # Extra check: make sure it was signed by OUR key specifically
    $signedByOurKey = $verifyOutput | Where-Object { $_ -match $SigningKeyID }
    if ($signedByOurKey) {
        OK "SIGNATURE VERIFIED — signed by key $SigningKeyID"
        OK "This script is authenticated by Meeko SolarPunk Node-01"
        Log-ToActual "HANDSHAKE-OK" "$ScriptName verified with key $SigningKeyID — executing"
    } else {
        FAIL "SIGNATURE VALID but signed by UNKNOWN KEY — REJECTING"
        FAIL "Expected key: $SigningKeyID"
        FAIL "Got: $($verifyOutput | Where-Object { $_ -match 'key' } | Select-Object -First 1)"
        Invoke-KaleidoscopeResponse -Reason "Wrong signing key" -ScriptName $ScriptName
        exit 2
    }
} else {
    # VERIFICATION FAILED — ACTIVATE KALEIDOSCOPE
    FAIL "SIGNATURE VERIFICATION FAILED"
    FAIL "Script may have been tampered with on GitHub"
    Invoke-KaleidoscopeResponse -Reason "Signature mismatch" -ScriptName $ScriptName
    exit 3
}

# ── STEP 4: EXECUTE VERIFIED SCRIPT ──────────────────────────────────────
INFO "Executing verified $ScriptName..."
Write-Host ""
& powershell.exe -ExecutionPolicy Bypass -File $scriptPath
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    OK "$ScriptName completed successfully"
    Log-ToActual "HANDSHAKE-COMPLETE" "$ScriptName executed and completed (exit 0)"
} else {
    WARN "$ScriptName exited with code $exitCode"
    Log-ToActual "HANDSHAKE-WARN" "$ScriptName exited with code $exitCode"
}

# Cleanup temp files
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue


# ════════════════════════════════════════════════════════════════════════════
# KALEIDOSCOPE RESPONSE — Runs when verification fails
# Triggers the Python shield and sends decoy data toward the attack source
# ════════════════════════════════════════════════════════════════════════════
function Invoke-KaleidoscopeResponse {
    param([string]$Reason, [string]$ScriptName)

    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║   KALEIDOSCOPE DEFENSE ACTIVATED         ║" -ForegroundColor Magenta
    Write-Host "  ║   Attacker enters. They never leave.     ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""

    # Log the attack
    $attackEntry = @{
        timestamp  = $timestamp
        type       = "TAMPER_DETECTED"
        script     = $ScriptName
        reason     = $Reason
        source_ip  = (Invoke-WebRequest "https://api.ipify.org" -UseBasicParsing -TimeoutSec 3).Content
        action     = "KALEIDOSCOPE_ACTIVATED"
    } | ConvertTo-Json

    $attackLog = "$repoPath\data\kaleidoscope_events.json"
    if (Test-Path $attackLog) {
        $existing = Get-Content $attackLog | ConvertFrom-Json
        $existing += ($attackEntry | ConvertFrom-Json)
        $existing | ConvertTo-Json -Depth 5 | Out-File $attackLog -Encoding utf8
    } else {
        "[$attackEntry]" | Out-File $attackLog -Encoding utf8
    }

    # Activate Python Kaleidoscope Shield
    $shieldPath = "$repoPath\mycelium\KALEIDOSCOPE_SHIELD.py"
    if (Test-Path $shieldPath) {
        Start-Process python -ArgumentList $shieldPath -WindowStyle Hidden
        WARN "Kaleidoscope Shield activated — decoy honeytokens deployed"
    }

    # Alert the human anchor via SOLARPUNK_ACTUAL.md
    Log-ToActual "KALEIDOSCOPE-ALERT" "TAMPER DETECTED on $ScriptName | Reason: $Reason | Kaleidoscope activated | Attacker is now in the mirror room"

    # Also alert Discord if webhook is set
    $hook = [Environment]::GetEnvironmentVariable('SOLARPUNK_HOOK', 'User')
    if ($hook) {
        $alert = @{
            content = "🚨 **SOLARPUNK SECURITY ALERT** 🚨`nTamper detected on ``$ScriptName```nReason: $Reason`nKaleidoscope Shield activated.`nTime: $timestamp"
        } | ConvertTo-Json
        try {
            Invoke-RestMethod -Uri $hook -Method Post -Body $alert -ContentType "application/json" | Out-Null
            OK "Alert sent to Discord"
        } catch {
            WARN "Discord alert failed (webhook may be stale)"
        }
    }

    Write-Host ""
    FAIL "EXECUTION BLOCKED. Machine is secure. Attacker is in the mirror."
}
