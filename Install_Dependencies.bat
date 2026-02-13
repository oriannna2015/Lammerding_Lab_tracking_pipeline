@echo off
REM Installation script for Lammerding Lab Cell Tracking Support
REM Author: Oriana Chen

echo ====================================
echo Lammerding Lab - Cell Tracking Support - Setup
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

echo Python version:
python --version
echo.

echo Installing dependencies...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Installation failed.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation complete!
echo ====================================
echo.
echo You can now run the GUI by:
echo.
echo   1. Double click "Launch_GUI.bat"
   2. Or run: python main.py
echo.
pause
