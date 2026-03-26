function mycelium {
    param([string]$Tool, [string]$Task)
    Write-Host "--- MEEKO-01: DISPATCHING $Tool ---" -ForegroundColor Green
    
    switch ($Tool) {
        "engineer" { # Calls Aider
            Set-Location "C:\AI-Automation\repos\aider"
            aider --message "$Task"
            Set-Location "C:\Users\meeko\Desktop\meeko-nerve-center"
        }
        "library" { # Opens AnythingLLM Workspace
            Start-Process "C:\AI-Automation\repos\anythingllm\AnythingLLM.exe"
            Write-Host "Opening Knowledge Vault..." -ForegroundColor Cyan
        }
        "map" { # Re-links the repos to the Nerve Center
            Write-Host "Linking AI-Automation Repos to Nerve Center..." -ForegroundColor Yellow
            New-Item -ItemType SymbolicLink -Path ".\repos" -Value "C:\AI-Automation\repos" -Force
        }
    }
}
