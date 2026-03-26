@echo off
echo ==========================================
echo  ATOMIC MYCELIUM - PORTABLE INSTALLER
echo ==========================================
echo.
echo This will install everything needed:
echo  - Chocolatey (package manager)
echo  - Python 3.12
echo  - Git
echo  - VS Code
echo  - Node.js
echo  - Docker Desktop
echo.
pause

echo.
echo [1/7] Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
call refreshenv

echo [2/7] Installing Python 3.12...
choco install python --version=3.12.0 -y
call refreshenv

echo [3/7] Installing Git...
choco install git -y

echo [4/7] Installing VS Code...
choco install vscode -y

echo [5/7] Installing Node.js...
choco install nodejs -y

echo [6/7] Installing Docker Desktop...
choco install docker-desktop -y

echo [7/7] Installing WSL (for Docker)...
wsl --install

echo.
echo ==========================================
echo  BASE SOFTWARE INSTALLED
echo.
echo IMPORTANT: You may need to REBOOT now
echo if Docker or WSL prompted for it.
echo.
echo After reboot, run SETUP.bat
echo ==========================================
pause
