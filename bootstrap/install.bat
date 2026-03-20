@echo off
setlocal
chcp 65001 > nul

:: ============================================================================
:: Minimal Bootstrap for the Python-based ComfyUI Installer
:: This script checks for Python and launches the Python CLI.
:: ============================================================================

title UmeAiRT ComfyUI Installer (Python)
echo.
echo ============================================================================
echo          UmeAiRT ComfyUI Installer - Python Edition
echo ============================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://python.org
    echo.
    pause
    exit /b 1
)

:: Check Python version is 3.11+
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
echo [INFO] Found Python %PY_VERSION%

:: Set install path
set "InstallPath=%~dp0"
if "%InstallPath:~-1%"=="\" set "InstallPath=%InstallPath:~0,-1%"

:: Install the Python package if not already installed (in an isolated venv)
if not exist "%InstallPath%\.installer_venv" (
    echo [INFO] Creating isolated installer environment...
    python -m venv "%InstallPath%\.installer_venv"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Installing comfyui-installer dependencies...
    "%InstallPath%\.installer_venv\Scripts\pip.exe" install -e "%InstallPath%" --quiet
)

:: Launch the CLI
echo [INFO] Launching installer...
"%InstallPath%\.installer_venv\Scripts\python.exe" -m src.cli install --path "%InstallPath%"

pause
