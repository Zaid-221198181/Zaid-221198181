# Quick Setup Script for Marketplace Backend
# Run this in PowerShell from c:\Zaid_AI

Write-Host "=== Setting up Marketplace Backend ===" -ForegroundColor Cyan

# 1. Create virtualenv
Set-Location "C:\Zaid_AI\marketplace-backend"
python -m venv venv

# 2. Activate and install dependencies
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Create PostgreSQL database
Write-Host "`nPlease ensure PostgreSQL is running, then press Enter..." -ForegroundColor Yellow
Read-Host

# Create database using psql
$env:PGPASSWORD = "password"
psql -U postgres -c "CREATE DATABASE marketplace_db;" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database created successfully!" -ForegroundColor Green
} else {
    Write-Host "Database may already exist, continuing..." -ForegroundColor Yellow
}

# 4. Start server
Write-Host "`n=== Starting FastAPI server ===" -ForegroundColor Cyan
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "Swagger docs at:          http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Android emulator URL:     http://10.0.2.2:8000" -ForegroundColor Green
uvicorn main:app --reload --host 0.0.0.0 --port 8000
