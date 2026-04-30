@echo off
REM ============================================
REM  CellTracker Pro - One-Click Launcher
REM  Double-click this file to start the app.
REM ============================================

cd /d "%~dp0"

REM Check if local venv exists
if exist "cell_tracking_pipeline\Scripts\activate.bat" (
    echo [OK] Virtual environment found.
    call "cell_tracking_pipeline\Scripts\activate.bat"
    goto :launch
)

REM No local venv - create one
echo ============================================
echo  Setting up Python environment...
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.8 or higher and add to PATH.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv cell_tracking_pipeline
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Activating environment...
call "cell_tracking_pipeline\Scripts\activate.bat"

echo [3/3] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [OK] Environment setup complete!
echo ============================================
echo.

:launch
REM Launch the application
python main.py

REM If there was an error, pause so user can read it
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
