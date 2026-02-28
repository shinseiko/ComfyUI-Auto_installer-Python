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

# Check for Python 3
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

# Set install path to script directory
INSTALL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install the Python package if not already installed
if ! $PYTHON -c "import src" 2>/dev/null; then
    echo "[INFO] Installing comfyui-installer package..."
    $PYTHON -m pip install -e "$INSTALL_PATH" --quiet
fi

# Launch the installer CLI
echo "[INFO] Starting installation..."
echo ""
comfyui-installer install --path "$INSTALL_PATH"
