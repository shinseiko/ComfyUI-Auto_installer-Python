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

USER umeairt

# Copy the installer repository into the container
COPY --chown=umeairt:umeairt . /app

# Pre-install ComfyUI during the image build phase.
# This downloads PyTorch, clones repositories, and pre-populates the external linked folders.
# (If building on a machine without a GPU, it detects CPU and installs fallback CPU wheels,
# making the build safe on standard CI runners).
RUN python -m src.cli install --path /app --type venv --yes

# Give execution permission to the entrypoint
RUN chmod +x /app/entrypoint.sh

# Expose the standard ComfyUI web port
EXPOSE 8188

# Launch the wrapper
ENTRYPOINT ["/app/entrypoint.sh"]
