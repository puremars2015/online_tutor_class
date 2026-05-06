$ErrorActionPreference = "Stop"

Write-Host "=== Initialize Project ===" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "`n[1/3] Starting Docker SQL Server..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker start failed. Please ensure Docker Desktop is running." -ForegroundColor Red
    exit 1
}

Write-Host "Waiting for SQL Server..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n[2/3] Installing backend Python dependencies..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\backend"
python -m pip install --upgrade pip
python -m pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors python-dotenv werkzeug pyodbc
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python dependencies installation failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/3] Initializing database..." -ForegroundColor Yellow
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database initialization failed." -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot
Write-Host "`n=== Initialization Complete ===" -ForegroundColor Green
Write-Host "Default admin: admin@example.com / admin123" -ForegroundColor Cyan