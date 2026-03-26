Write-Host "--- SIA HEARTBEAT STARTING ---" -ForegroundColor Cyan
git pull origin main --rebase

# Launch the Intelligence Swarm
python C:\Solarpunk-Prime\mycelium\swarm_scout.py

# Auto-Commit and Amplify
git add .
git commit -m "SIA: Autonomous Pulse - Growth Recorded"
git push origin main

Write-Host "--- SIA HEARTBEAT COMPLETE ---" -ForegroundColor Green
