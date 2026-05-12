@echo off
title HVAC Complaint Analysis System
echo ============================================
echo   HVAC Complaint Analysis System
echo   AI-Powered Dashboard
echo ============================================
echo.

set PYTHONUTF8=1

:: Check if database exists
if not exist "backend\data\complaints.db" (
    echo [WARN] No database found. Running first-time setup...
    call setup.bat
)

echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.

:: Open browser after 2 second delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Start the server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
