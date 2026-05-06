$ErrorActionPreference = "Stop"

Write-Host "=== Starting Services ===" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "`n[1/2] Starting SQL Server (Docker)..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker start failed. Please ensure Docker Desktop is running." -ForegroundColor Red
    exit 1
}
Write-Host "SQL Server started (port 1433)" -ForegroundColor Green

Write-Host "`n[2/2] Starting Flask backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\backend'; python run.py"

Write-Host "`n=== All Services Started ===" -ForegroundColor Green
Write-Host "Backend: http://localhost:5000" -ForegroundColor Cyan
Write-Host "`nAdmin: admin@example.com / admin123" -ForegroundColor Yellow