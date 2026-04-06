@echo off
REM ============================================
REM SolarPunk Autonomic Nerve -- Background Launcher
REM ============================================
REM Keeps the system alive when Claude sessions end.
REM Uses local Ollama AI for decisions.
REM
REM Usage:
REM   start_autonomic.bat          -- Run in foreground (see output)
REM   start_autonomic.bat --bg     -- Run in background (no window)
REM   start_autonomic.bat --once   -- Single heartbeat then exit
REM ============================================

cd /d "%~dp0"

if "%1"=="--bg" (
    echo Starting Autonomic Nerve in background...
    start /B pythonw mycelium/AUTONOMIC_NERVE.py
    echo PID launched. Check data/autonomic_state.json for status.
    echo Logs: data/logs/autonomic_*.log
    goto :eof
)

if "%1"=="--once" (
    python mycelium/AUTONOMIC_NERVE.py --once
    goto :eof
)

echo ============================================
echo   SolarPunk Autonomic Nerve
echo   Press Ctrl+C to stop
echo ============================================
python mycelium/AUTONOMIC_NERVE.py
