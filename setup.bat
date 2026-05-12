@echo off
title HVAC Complaint Analysis System - First Time Setup
echo ============================================
echo   HVAC Complaint Analysis System - Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Generating synthetic complaint data (2500 records)...
cd backend
set PYTHONUTF8=1
python generate_data.py
if errorlevel 1 (
    echo [ERROR] Data generation failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Running ML analysis pipeline...
python run_pipeline.py
if errorlevel 1 (
    echo [ERROR] ML pipeline failed.
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   Run 'start.bat' to launch the dashboard.
echo.
pause
