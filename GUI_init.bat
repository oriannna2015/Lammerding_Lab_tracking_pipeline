@echo off
REM Launcher for Lammerding Lab Cell Tracking Support
REM Author: Oriana Chen

echo ====================================
echo Lammerding Lab - Cell Tracking Support
echo ====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo.
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Starting GUI...
echo.

REM Run the GUI
python main.py

REM If GUI crashed, pause to see error
if errorlevel 1 (
    echo.
    echo An error occurred.
    pause
)
