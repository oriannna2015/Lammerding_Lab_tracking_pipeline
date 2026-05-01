@echo off
setlocal EnableDelayedExpansion

echo ====================================================
echo   CellTracker Pro - Lammerding Lab
echo ====================================================
echo.

REM --- Verify Python is reachable (assumes environment is already activated) ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo.
    echo Please activate your Python environment first, then run this script again.
    echo.
    echo   conda:  conda activate ^<env_name^>
    echo   venv:   ^<env_folder^>\Scripts\activate
    echo.
    echo See README.md - Installation section for setup instructions.
    echo.
    pause
    exit /b 1
)

REM --- Check that required packages are installed ---
echo Checking environment...
python -c "import bottle, numpy, pandas, tifffile, stardist" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] One or more required packages are missing.
    echo.
    echo Make sure your environment is activated and run Install_Dependencies.bat
    echo to install all dependencies, or refer to README.md - Installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Environment ready.
echo.
echo Starting CellTracker Pro...
echo.

REM --- Launch GUI ---
cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    echo Please refer to README.md - Troubleshooting for help.
    pause
)

endlocal
