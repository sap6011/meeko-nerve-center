while($true) {
    git pull origin main --rebase --quiet
    git push origin main --quiet
    Start-Sleep -Seconds 30
}
