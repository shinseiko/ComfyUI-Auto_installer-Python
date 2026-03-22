# syntax=docker/dockerfile:1.4
# ── Stage 1: Builder — install everything, compile, then clean up ──
FROM nvidia/cuda:13.0.2-runtime-ubuntu24.04 AS builder

# VARIANT controls the image flavor:
#   standard (default) → ComfyUI only
#   cloud              → ComfyUI + JupyterLab (for RunPod / cloud)
ARG VARIANT=standard

# Install system dependencies + build tools in a single layer
# build-essential and python3.12-dev are needed for compilation only
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    git \
    build-essential \
    aria2 \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/lib/python3.12/EXTERNALLY-MANAGED

# Install uv as a standalone binary
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv \
    && rm -rf /root/.local/bin  # clean installer leftovers

# Install Python 3.13 via uv for the ComfyUI venv
RUN uv python install 3.13

# Configure workspace
WORKDIR /app

# Ensure /app and /data are owned by UID 1000
RUN chown -R 1000:1000 /app && mkdir -p /data && chown -R 1000:1000 /data

# Declare /data as a volume
VOLUME /data

# Copy the installer repository into the container
COPY --chown=1000:1000 . /app

# Install the installer package system-wide
RUN uv pip install --system -e .

# Cloud variant: install JupyterLab
RUN if [ "$VARIANT" = "cloud" ]; then \
      echo "Installing JupyterLab (cloud variant)..." && \
      uv pip install --system jupyterlab; \
    else \
      echo "Standard variant — skipping JupyterLab."; \
    fi

# Switch to non-root user for the build phase
USER 1000

# Pre-install ComfyUI core (PyTorch, requirements, venv)
# Custom nodes are NOT installed here (--skip-nodes) — installed at runtime.
RUN python -m src.cli install --path /app --type venv --yes --cuda cu130 --skip-nodes

# ── Back to root for cleanup ──
USER 0

# Remove build-only packages and clean all caches in a single layer
# This saves ~500 MB by removing compilers, headers, and caches
RUN apt-get purge -y --auto-remove \
      build-essential \
      python3.12-dev \
      cpp gcc g++ make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/uv \
    && rm -rf /root/.cache/pip \
    && rm -rf /home/*/.cache/uv \
    && rm -rf /home/*/.cache/pip \
    && rm -rf /tmp/* \
    && find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /app -name "*.pyc" -delete 2>/dev/null || true

# Fix line endings and set executable
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Switch back to non-root user
USER 1000

# Expose ComfyUI (8188) and JupyterLab (8888, cloud variant only)
EXPOSE 8188 8888

# Launch the wrapper
ENTRYPOINT ["/app/entrypoint.sh"]
