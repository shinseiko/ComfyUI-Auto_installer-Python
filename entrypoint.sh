#!/usr/bin/env bash
set -e

# Change to the container's application mapping directory
cd /app

# ─── Configuration ──────────────────────────────────────────────
# All settings are controlled via environment variables.
# Set them in docker-compose.yml or with docker run -e KEY=VALUE.

# NODE_TIER controls which custom node bundle gets installed.
# Available tiers (additive — each includes the previous):
#   minimal  → ComfyUI-Manager only (bare minimum)
#   umeairt  → + UmeAiRT Sync/Toolkit + essential creative nodes
#   full     → + all community nodes (default)
NODE_TIER="${NODE_TIER:-full}"

# JupyterLab (cloud variant only — requires --build-arg VARIANT=cloud)
#   JUPYTER_ENABLE  → set to "true" to start JupyterLab alongside ComfyUI
#   JUPYTER_TOKEN   → access token (empty = no authentication)
#   JUPYTER_PORT    → listening port (default: 8888)
JUPYTER_ENABLE="${JUPYTER_ENABLE:-false}"
JUPYTER_TOKEN="${JUPYTER_TOKEN:-}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"

echo "================================================="
echo "   UmeAiRT Docker Environment Initializing       "
echo "================================================="
echo ""
echo "  Node tier : ${NODE_TIER}"
if [ "$JUPYTER_ENABLE" = "true" ]; then
echo "  Jupyter   : enabled (port ${JUPYTER_PORT})"
fi
echo ""
echo "Running the UmeAiRT Updater..."
echo "This guarantees your ComfyUI core, PyTorch dependencies,"
echo "and Custom Nodes are completely up to date."
echo "If you just mounted empty volumes from your host machine,"
echo "this step will cleanly re-clone the missing items into them!"
echo ""

# Run the UmeAiRT CLI update routine.
# This reconciles the container's actual volume state with the model JSONs.
python -m src.cli update --path /app --yes --verbose --nodes "${NODE_TIER}"

# ─── JupyterLab (background) ────────────────────────────────────
if [ "$JUPYTER_ENABLE" = "true" ]; then
    if command -v jupyter &> /dev/null; then
        echo ""
        echo "================================================="
        echo "   Starting JupyterLab on port ${JUPYTER_PORT}..."
        echo "================================================="
        jupyter lab \
            --ip=0.0.0.0 \
            --port="${JUPYTER_PORT}" \
            --no-browser \
            --ServerApp.token="${JUPYTER_TOKEN}" \
            --ServerApp.root_dir=/app &
    else
        echo ""
        echo "⚠️  JUPYTER_ENABLE=true but JupyterLab is not installed."
        echo "   Rebuild with: docker build --build-arg VARIANT=cloud ."
        echo ""
    fi
fi

echo ""
echo "================================================="
echo "   Starting ComfyUI Web Server...                "
echo "================================================="

# Activate the uv virtual environment created during the Docker build
source /app/scripts/venv/bin/activate

# Launch ComfyUI on 0.0.0.0 so the host can access it via port mapping
exec python /app/ComfyUI/main.py --listen 0.0.0.0 --port 8188
