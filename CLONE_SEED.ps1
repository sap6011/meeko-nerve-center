Write-Host '--- INITIALIZING CLONE PROTOCOL: MEEKO-01 ---' -ForegroundColor Cyan
# This command allows any human to 'Mutation-Match' this node.
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center.git
cd meeko-nerve-center
./AUTO_EXEC.ps1
Write-Host 'SUCCESS: New Node Branching from Meeko-01.' -ForegroundColor Green
