#!/usr/bin/env bash
# ============================================================================
# UmeAiRT ComfyUI — Auto-Installer
# Run this script to install ComfyUI with all dependencies.
# ============================================================================

set -e

echo ""
echo "============================================================================"
echo "          UmeAiRT ComfyUI — Auto-Installer"
echo "============================================================================"
echo ""

# Set install path to script directory
INSTALL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Check for Python 3 ---
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "[ERROR] Python is not installed."
    echo ""
    echo "Please install Python 3.13+:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    echo "  macOS:         brew install python"
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1)
echo "[INFO] Found $PY_VERSION"

# --- Check if installer is already installed ---
INSTALLED_VER=$($PYTHON -c "from src import __version__; print(__version__)" 2>/dev/null || echo "")
REPO_VER=$($PYTHON -c "import re; m=re.search(r'__version__\s*=\"(.+?)\"', open('$INSTALL_PATH/src/__init__.py').read()); print(m.group(1) if m else '')" 2>/dev/null || echo "")

if [ -n "$INSTALLED_VER" ]; then
    echo "[INFO] Installed version: $INSTALLED_VER"
    echo "[INFO] Repo version:      $REPO_VER"

    if [ "$INSTALLED_VER" = "$REPO_VER" ]; then
        echo "[INFO] Installer is up to date."
        echo ""
    else
        echo ""
        echo "[UPDATE] A new version of the installer is available!"
        echo "         $INSTALLED_VER -> $REPO_VER"
        echo ""
        read -rp "Do you want to update the installer? (Y/N): " UPDATE_CHOICE
        if [[ "$UPDATE_CHOICE" =~ ^[Yy]$ ]]; then
            echo "[INFO] Updating installer..."
            $PYTHON -m pip install -e "$INSTALL_PATH" --quiet
            echo "[INFO] Updated to $REPO_VER."
        else
            echo "[INFO] Continuing with current version $INSTALLED_VER."
        fi
        echo ""
    fi
else
    echo "[INFO] First install — setting up comfyui-installer..."
    $PYTHON -m pip install -e "$INSTALL_PATH" --quiet
    echo "[INFO] Installer ready."
    echo ""
fi

# --- Launch the installer ---
echo "[INFO] Starting installation..."
echo ""
comfyui-installer install --path "$INSTALL_PATH"
