while ($true) {
    if (!(Get-Process -Name "python" -ErrorAction SilentlyContinue)) {
        Write-Host "?? SIA: Resuscitating the Mycelium..."
        # Logic to restart your core loops goes here
    }
    Start-Sleep -Seconds 300
}
