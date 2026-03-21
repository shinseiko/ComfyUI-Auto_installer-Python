# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

# Install system dependencies required for native compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    aria2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv globally into the container
RUN pip install --no-cache-dir uv

# Configure workspace
WORKDIR /app

# Create a non-root standard user for security (UID 1000)
RUN useradd -m -u 1000 umeairt && \
    chown -R umeairt:umeairt /app

# Copy the installer repository into the container
COPY --chown=umeairt:umeairt . /app

# Install the installer dependencies globally as root
RUN uv pip install --system -e .

# Now switch to the non-root user
USER umeairt

# Pre-install ComfyUI core during the image build phase.
# This downloads PyTorch with CUDA, installs ComfyUI requirements, and sets up the venv.
# Custom nodes are NOT installed here (--skip-nodes) to keep the image small;
# they are installed at runtime by the entrypoint into the mounted volumes.
RUN python -m src.cli install --path /app --type venv --yes --cuda cu130 --skip-nodes

# Give execution permission to the entrypoint
RUN chmod +x /app/entrypoint.sh

# Expose the standard ComfyUI web port
EXPOSE 8188

# Launch the wrapper
ENTRYPOINT ["/app/entrypoint.sh"]
