# Script om alle data te verwijderen
Write-Host "Verwijderen van alle data..." -ForegroundColor Yellow

# Database verwijderen
if (Test-Path "data\analyses.db") {
    Remove-Item "data\analyses.db" -Force
    Write-Host "Database verwijderd" -ForegroundColor Green
}

# Training images verwijderen
if (Test-Path "data\training_images") {
    Remove-Item "data\training_images" -Recurse -Force
    Write-Host "Training images verwijderd" -ForegroundColor Green
}

# Reference photos verwijderen
if (Test-Path "data\reference_photos") {
    Remove-Item "data\reference_photos" -Recurse -Force
    Write-Host "Reference photos verwijderd" -ForegroundColor Green
}

# Exports verwijderen
if (Test-Path "data\exports") {
    Remove-Item "data\exports" -Recurse -Force
    Write-Host "Exports verwijderd" -ForegroundColor Green
}

# Training exports verwijderen
if (Test-Path "data\training_exports") {
    Remove-Item "data\training_exports" -Recurse -Force
    Write-Host "Training exports verwijderd" -ForegroundColor Green
}

# Temp exports verwijderen
Get-ChildItem -Path "data" -Filter "temp_export_*" -Directory | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "$($_.Name) verwijderd" -ForegroundColor Green
}

# Uploads verwijderen
if (Test-Path "uploads") {
    Remove-Item "uploads" -Recurse -Force
    Write-Host "Uploads verwijderd" -ForegroundColor Green
}

Write-Host ""
Write-Host "Alle data verwijderd!" -ForegroundColor Green
Write-Host "Herstart de backend om de database opnieuw te initialiseren." -ForegroundColor Cyan
