function Export-SolarPunk-City {
    Write-Host "--- ARCHITECTING 3D SOLARPUNK CITY ---" -ForegroundColor Magenta
    $Files = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch 'node_modules|.git' }
    
    $CityData = foreach ($File in $Files) {
        [PSCustomObject]@{
            Name = $File.Name
            Path = $File.DirectoryName
            Size = $File.Length
            Complexity = (Get-Content $File.FullName | Measure-Object -Line).Lines
            Heat = if ($File.Name -match 'logic') { "High" } else { "Stable" }
        }
    }
    
    $CityData | ConvertTo-Json | Out-File -FilePath "SOLARPUNK_CITY_MAP.json"
    Write-Host "MAP EXPORTED: Open this in any 2026 WebGL viewer (e.g., City-Blocks or CodeCohesion)." -ForegroundColor Green
}
