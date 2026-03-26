Write-Host "--- SIA MIRROR LOOP: SELF-BUILDING ACTIVE ---" -ForegroundColor Green
# 1. Pull latest emails
# 2. Run mirror_node.py to check for 'build', 'need', or 'want'
# 3. If SolarPunk wants something, it writes the script to C:\Solarpunk-Prime\projects\autobuild\
python C:\Solarpunk-Prime\mycelium\mirror_node.py
