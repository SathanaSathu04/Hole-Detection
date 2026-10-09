@echo off
echo ===================================================
echo Starting Textile Thread Insertion System...
echo ===================================================

echo [1/2] Launching Python FastAPI Backend on http://127.0.0.1:8000 ...
start "Textile Machine Backend (FastAPI)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\Activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/2] Launching Angular Frontend on http://localhost:4200 ...
start "Textile Machine Frontend (Angular)" cmd /k "cd /d %~dp0frontend && npm start"

echo ===================================================
echo Both Backend and Frontend are starting!
echo Backend Docs:  http://127.0.0.1:8000/docs
echo Frontend Web:  http://localhost:4200
echo ===================================================
