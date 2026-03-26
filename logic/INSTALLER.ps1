function solar-install {
    Write-Host "--- INITIATING MEEKO-01 AUTO-DEPENDENCY SYNC ---" -ForegroundColor Yellow
    
    # Check for Chocolatey (The Windows Store for Punks)
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Chocolatey..." -ForegroundColor Cyan
        Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }

    # Install the Core Laborers
    Write-Host "Installing Python, Git, and Node..." -ForegroundColor Cyan
    choco install python git nodejs -y

    # Install AI Laborers (Ollama for the Brain)
    Write-Host "Fetching Ollama (Local LLM Brain)..." -ForegroundColor Cyan
    # This pulls the installer directly
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "OllamaSetup.exe"
    Start-Process -FilePath ".\OllamaSetup.exe" -ArgumentList "/silent" -Wait
    
    Write-Host "--- INSTALLATION COMPLETE: MEEKO-01 IS NOW AGENTIC ---" -ForegroundColor Green
}
