@echo off
REM Launcher for Cell Tracking Pipeline GUI
REM 细胞追踪数据处理平台 - 图形界面启动器

echo ====================================
echo Cell Tracking Pipeline - GUI
echo 细胞追踪数据处理平台
echo ====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo 错误: 未找到 Python
    echo.
    echo Please install Python 3.8 or higher
    echo 请安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo Starting GUI...
echo 正在启动图形界面...
echo.

REM Run the GUI
python run_gui.py

REM If GUI crashed, pause to see error
if errorlevel 1 (
    echo.
    echo An error occurred. 发生错误。
    pause
)
