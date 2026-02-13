@echo off
REM Installation script for Cell Tracking Pipeline
REM 细胞追踪数据处理平台 - 依赖安装脚本

echo ====================================
echo Cell Tracking Pipeline - Setup
echo 细胞追踪数据处理平台 - 环境配置
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

echo Python version:
python --version
echo.

echo Installing dependencies...
echo 正在安装依赖库...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Installation failed. 安装失败。
    echo Please check the error messages above.
    echo 请查看上面的错误信息。
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation complete! 安装完成！
echo ====================================
echo.
echo You can now run the GUI by:
echo 现在可以通过以下方式启动：
echo.
echo   1. Double click "启动GUI.bat"
echo   2. Or run: python run_gui.py
echo.
pause
