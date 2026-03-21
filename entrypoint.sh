#!/usr/bin/env bash
set -e

# Change to the container's application mapping directory
cd /app

echo "================================================="
echo "   UmeAiRT Docker Environment Initializing       "
echo "================================================="
echo ""
echo "Running the UmeAiRT Updater..."
echo "This guarantees your ComfyUI core, PyTorch dependencies,"
echo "and Custom Nodes are completely up to date."
echo "If you just mounted empty volumes from your host machine,"
echo "this step will cleanly re-clone the missing items into them!"
echo ""

# Run the UmeAiRT CLI update routine.
# This reconciles the container's actual volume state with the model JSONs.
python -m src.cli update --path /app --yes --verbose

echo ""
echo "================================================="
echo "   Starting ComfyUI Web Server...                "
echo "================================================="

# Activate the uv virtual environment created during the Docker build
source /app/scripts/venv/bin/activate

# Launch ComfyUI on 0.0.0.0 so the host can access it via port mapping
exec python /app/ComfyUI/main.py --listen 0.0.0.0 --port 8188
