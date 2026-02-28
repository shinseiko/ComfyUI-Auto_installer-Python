@echo off
setlocal
chcp 65001 > nul

:: ============================================================================
:: UmeAiRT ComfyUI — Auto-Installer
:: Double-click this file to install ComfyUI with all dependencies.
:: ============================================================================

title UmeAiRT ComfyUI Installer
echo.
echo ============================================================================
echo           UmeAiRT ComfyUI — Auto-Installer
echo ============================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.13 from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
echo [INFO] Found Python %PY_VERSION%

:: Set install path to where this script is located
set "InstallPath=%~dp0"
if "%InstallPath:~-1%"=="\" set "InstallPath=%InstallPath:~0,-1%"

:: Install the Python package if not already installed
python -c "import src" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing comfyui-installer package...
    pip install -e "%InstallPath%" --quiet
)

:: Launch the installer CLI
echo [INFO] Starting installation...
echo.
comfyui-installer install --path "%InstallPath%"

pause
