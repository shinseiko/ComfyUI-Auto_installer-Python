@echo off
setlocal EnableDelayedExpansion
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

:: Set install path to where this script is located
set "InstallPath=%~dp0"
if "%InstallPath:~-1%"=="\" set "InstallPath=%InstallPath:~0,-1%"

:: --- Check for Python ---
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

:: --- Check if installer is already installed ---
set "INSTALLED_VER="
for /f "delims=" %%v in ('python -c "from src import __version__; print(__version__)" 2^>nul') do set "INSTALLED_VER=%%v"

:: Get repo version
set "REPO_VER="
for /f "delims=" %%v in ('python -c "import re; m=re.search(r'__version__\s*=\s*\"(.+?)\"', open(r'%InstallPath%\src\__init__.py').read()); print(m.group(1) if m else '')" 2^>nul') do set "REPO_VER=%%v"

if defined INSTALLED_VER (
    echo [INFO] Installed version: %INSTALLED_VER%
    echo [INFO] Repo version:      %REPO_VER%

    if "%INSTALLED_VER%"=="%REPO_VER%" (
        echo [INFO] Installer is up to date.
        echo.
    ) else (
        echo.
        echo [UPDATE] A new version of the installer is available!
        echo          %INSTALLED_VER% -^> %REPO_VER%
        echo.
        set /p "UPDATE_CHOICE=Do you want to update the installer? (Y/N): "
        if /i "!UPDATE_CHOICE!"=="Y" (
            echo [INFO] Updating installer...
            pip install -e "%InstallPath%" --quiet
            echo [INFO] Updated to %REPO_VER%.
        ) else (
            echo [INFO] Continuing with current version %INSTALLED_VER%.
        )
        echo.
    )
) else (
    echo [INFO] First install — setting up comfyui-installer...
    pip install -e "%InstallPath%" --quiet
    echo [INFO] Installer ready.
    echo.
)

:: --- Launch the installer ---
echo [INFO] Starting installation...
echo.
comfyui-installer install --path "%InstallPath%"

pause
