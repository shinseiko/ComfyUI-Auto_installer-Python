# syntax=docker/dockerfile:1.4
# ──────────────────────────────────────────────────────────────────
# UmeAiRT ComfyUI Docker Image
#
# Variants (set via --build-arg VARIANT=...):
#   standard      → ComfyUI with pre-installed PyTorch venv (default)
#   cloud         → standard + JupyterLab
#   lite          → Minimal image — installs PyTorch on first run (~1.5 GB)
#   lite-cloud    → lite + JupyterLab
# ──────────────────────────────────────────────────────────────────

# ── Stage 1: BUILDER ─────────────────────────────────────────────
FROM nvidia/cuda:13.0.2-runtime-ubuntu24.04 AS builder

ARG VARIANT=standard

# Install ALL dependencies (including build tools for compilation)
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

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv

# Install Python 3.13 via uv
RUN uv python install 3.13

WORKDIR /app
RUN chown -R 1000:1000 /app && mkdir -p /data && chown -R 1000:1000 /data
COPY --chown=1000:1000 . /app

# Install the installer CLI system-wide
RUN uv pip install --system -e .

# Cloud variants: install JupyterLab
RUN if [ "$VARIANT" = "cloud" ] || [ "$VARIANT" = "lite-cloud" ]; then \
      uv pip install --system jupyterlab; \
    fi

USER 1000

# Pre-install ComfyUI + PyTorch venv (standard/cloud only)
# Lite variants SKIP this — PyTorch is installed at first runtime via entrypoint.
RUN if [ "$VARIANT" = "standard" ] || [ "$VARIANT" = "cloud" ]; then \
      python -m src.cli install --path /app --type venv --yes --cuda cu130 --skip-nodes; \
    else \
      echo "Lite variant — skipping pre-install (will install at first run)."; \
    fi

# Clean caches
USER 0
RUN rm -rf /root/.cache/uv /root/.cache/pip /home/*/.cache/uv /home/*/.cache/pip /tmp/* \
    && find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /app -name "*.pyc" -delete 2>/dev/null || true

# ── Stage 2: RUNTIME ─────────────────────────────────────────────
FROM nvidia/cuda:13.0.2-runtime-ubuntu24.04

ARG VARIANT=standard

# Install ONLY runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    aria2 \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/lib/python3.12/EXTERNALLY-MANAGED

# Copy uv binary from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy uv-managed Python 3.13 from builder
COPY --from=builder /root/.local/share/uv /root/.local/share/uv

# Copy system-wide Python packages (installer CLI, jupyterlab if cloud)
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages

# Copy the app (with or without pre-installed venv depending on variant)
WORKDIR /app
COPY --from=builder --chown=1000:1000 /app /app
COPY --from=builder --chown=1000:1000 /data /data

# Store the variant name so the entrypoint knows if first-run install is needed
RUN echo "$VARIANT" > /app/.docker_variant

VOLUME /data

# Fix line endings and set executable
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

USER 1000

EXPOSE 8188 8888

ENTRYPOINT ["/app/entrypoint.sh"]
