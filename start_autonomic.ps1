# ============================================
# SolarPunk Autonomic Nerve -- PowerShell Launcher
# ============================================
# Runs SolarPunk's heartbeat daemon.
# Thermal-aware: auto-throttles when machine is hot.
# Uses local Ollama AI for decisions.
#
# Usage:
#   .\start_autonomic.ps1              -- Run in foreground
#   .\start_autonomic.ps1 -Background  -- Run in background
#   .\start_autonomic.ps1 -Once        -- Single heartbeat
#   .\start_autonomic.ps1 -Install     -- Install as startup task
# ============================================

param(
    [switch]$Background,
    [switch]$Once,
    [switch]$Install
)

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if ($Install) {
    Write-Host "Installing SolarPunk Autonomic Nerve as startup task..."
    $python = (Get-Command python).Source
    $script = Join-Path $RepoRoot "mycelium\AUTONOMIC_NERVE.py"

    $action = New-ScheduledTaskAction -Execute $python -Argument $script -WorkingDirectory $RepoRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartInterval (New-TimeSpan -Minutes 5) -RestartCount 3

    Register-ScheduledTask -TaskName "SolarPunk_Autonomic" -Action $action -Trigger $trigger -Settings $settings -Description "SolarPunk Autonomic Nerve - keeps the system alive 24/7 with thermal management" -Force

    Write-Host "Installed! SolarPunk will auto-start when you log in."
    Write-Host "To remove: Unregister-ScheduledTask -TaskName 'SolarPunk_Autonomic'"
    exit
}

if ($Once) {
    python mycelium\AUTONOMIC_NERVE.py --once
    exit
}

if ($Background) {
    Write-Host "Starting Autonomic Nerve in background..."
    $proc = Start-Process -FilePath python -ArgumentList "mycelium\AUTONOMIC_NERVE.py" -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru
    Write-Host "PID: $($proc.Id)"
    Write-Host "Check status: cat data\autonomic_state.json"
    Write-Host "Logs: data\logs\autonomic_*.log"
    exit
}

Write-Host "============================================"
Write-Host "  SolarPunk Autonomic Nerve"
Write-Host "  Thermal-aware | AI-powered | Never stops"
Write-Host "  Press Ctrl+C to stop"
Write-Host "============================================"
python mycelium\AUTONOMIC_NERVE.py
