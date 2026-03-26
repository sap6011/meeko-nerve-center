@echo off
echo ==========================================
echo  ATOMIC MYCELIUM - PROJECT SETUP
echo ==========================================
echo.

cd C:\

echo Creating project directory...
mkdir atomic-agents 2>nul
cd atomic-agents

echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing Python packages (this takes 2-3 minutes)...
pip install -r "%~dp0requirements.txt"

echo Creating directory structure...
mkdir src\core 2>nul
mkdir src\communication 2>nul
mkdir src\models 2>nul
mkdir src\tools 2>nul
mkdir src\mycelium\nodes 2>nul
mkdir src\mycelium\spore_bank 2>nul
mkdir src\finance\strategies 2>nul
mkdir src\finance\exchanges 2>nul
mkdir data\mycelium\growth_logs 2>nul
mkdir data\trades 2>nul
mkdir data\performance 2>nul

echo Copying source files...
xcopy /E /I /Y "%~dp0src\*" "C:\atomic-agents\src\"

echo Creating .env file...
copy "%~dp0.env.template" "C:\atomic-agents\.env"

echo Creating launcher...
(
echo cd C:\atomic-agents
echo call venv\Scripts\activate.bat
echo set PYTHONPATH=C:\atomic-agents\src
echo python -m src.main
echo pause
) > "C:\atomic-agents\start-mycelium.bat"

echo.
echo ==========================================
echo  SETUP COMPLETE!
echo.
echo NEXT STEPS:
echo  1. Edit C:\atomic-agents\.env
echo     - Add your Cerebras API key
echo     - Add your Supabase credentials
echo.
echo  2. Double-click start-mycelium.bat
echo.
echo  3. Type: spawn crypto 30
echo     Type: spawn stock 24
echo     Type: auto 30
echo.
echo ==========================================
pause
