Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Textile Thread Insertion System..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm start"

Write-Host "Both Backend and Frontend processes launched!" -ForegroundColor Green
Write-Host "Backend Docs : http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend UI   : http://localhost:4200" -ForegroundColor Yellow
