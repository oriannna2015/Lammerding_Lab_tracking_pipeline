@echo off
setlocal EnableDelayedExpansion

echo ====================================================
echo   CellTracker Pro - Environment Setup
echo   Lammerding Lab
echo ====================================================
echo.
echo This script will create a dedicated Python environment
echo and install all required packages.
echo.
echo If you encounter any errors, please refer to the
echo Installation section of README.md for guidance.
echo.

REM =====================================================
REM  Step 1: Choose environment manager
REM =====================================================
echo Select environment type:
echo   [1] conda   ^(recommended - requires Miniconda or Anaconda^)
echo   [2] venv    ^(built-in Python virtual environment^)
echo.
set /p ENV_TYPE="Enter 1 or 2: "

if "!ENV_TYPE!"=="1" goto :setup_conda
if "!ENV_TYPE!"=="2" goto :setup_venv

echo.
echo [ERROR] Invalid choice. Please enter 1 or 2.
pause
exit /b 1


REM =====================================================
REM  CONDA PATH
REM =====================================================
:setup_conda
echo.
set /p ENV_NAME="Enter a name for your conda environment (e.g. celltrack): "
if "!ENV_NAME!"=="" (
    echo [ERROR] Environment name cannot be empty.
    pause
    exit /b 1
)

conda --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] conda not found in PATH.
    echo Please install Miniconda ^(https://docs.conda.io/en/latest/miniconda.html^)
    echo or Anaconda, then re-run this script.
    echo.
    echo See README.md - Installation section for details.
    pause
    exit /b 1
)

echo.
echo Creating conda environment "!ENV_NAME!" with Python 3.9...
conda create -n "!ENV_NAME!" python=3.9 -y
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create conda environment.
    echo Please refer to README.md - Installation for troubleshooting.
    pause
    exit /b 1
)

echo.
echo Installing dependencies into "!ENV_NAME!"...
call conda run -n "!ENV_NAME!" python -m pip install --upgrade pip
call conda run -n "!ENV_NAME!" python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo Please refer to README.md - Installation for troubleshooting.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   Setup Complete!
echo ====================================================
echo.
echo Conda environment "!ENV_NAME!" is ready.
echo.
echo IMPORTANT - Before launching CellTracker Pro, activate
echo your environment by running:
echo.
echo     conda activate !ENV_NAME!
echo.
echo Then double-click CellTracker_Pro.bat to start the GUI.
echo.
pause
exit /b 0


REM =====================================================
REM  VENV PATH
REM =====================================================
:setup_venv
echo.
set /p ENV_NAME="Enter a folder name for the virtual environment (e.g. celltrack_env): "
if "!ENV_NAME!"=="" (
    echo [ERROR] Environment name cannot be empty.
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.8 or higher ^(https://www.python.org/downloads/^).
    echo.
    echo See README.md - Installation section for details.
    pause
    exit /b 1
)

set "ENV_PATH=%~dp0!ENV_NAME!"
echo.
echo Creating virtual environment at:
echo   !ENV_PATH!

python -m venv "!ENV_PATH!"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create virtual environment.
    echo Please refer to README.md - Installation for troubleshooting.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
"!ENV_PATH!\Scripts\python.exe" -m pip install --upgrade pip
"!ENV_PATH!\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo Please refer to README.md - Installation for troubleshooting.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   Setup Complete!
echo ====================================================
echo.
echo Virtual environment "!ENV_NAME!" is ready.
echo.
echo IMPORTANT - Before launching CellTracker Pro, activate
echo your environment by running:
echo.
echo     !ENV_PATH!\Scripts\activate
echo.
echo Then double-click CellTracker_Pro.bat to start the GUI.
echo.
pause
exit /b 0

endlocal
