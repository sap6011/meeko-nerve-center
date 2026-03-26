function build {
    param([string]$ProjectName, [string]$Instruction)
    Write-Host "--- SOLAR-PUNK CORE: BUILDING $ProjectName ---" -ForegroundColor Green
    
    # Ensure the directory exists
    $BuildPath = "C:\Users\meeko\Desktop\$ProjectName"
    if (!(Test-Path $BuildPath)) { New-Item -ItemType Directory -Path $BuildPath }

    # Call the Engineer (Aider)
    # We use 'aider' directly since it should be in your PATH from the repo install
    Set-Location "C:\AI-Automation\repos\aider"
    aider --message "Targeting folder $BuildPath. Task: $Instruction. Build it now."
    Set-Location "C:\Users\meeko\Desktop\meeko-nerve-center"
}
