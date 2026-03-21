# ComfyUI Auto-Installer

Cross-platform Python CLI to fully automate the installation, update, and configuration of [ComfyUI](https://github.com/comfyanonymous/ComfyUI).

## Highlights

- **One-Click Install** — Double-click `Install.bat` (Windows) or run `Install.sh` (Linux/macOS)
- **Cross-Platform** — Windows (CUDA/DirectML), Linux (CUDA/ROCm), macOS (MPS)
- **GPU Optimizations** — Triton, SageAttention, xformers with version compatibility
- **34 Curated Custom Nodes** — Additive manifest — never removes user-installed nodes
- **Model Catalog v3** — 7 model families with VRAM-based recommendations and SHA-256 integrity
- **Junction Architecture** — User data persists independently from ComfyUI updates
- **Model Security Scanner** — Detects malicious pickle code via `picklescan`

## Quick Start

=== "Windows (PowerShell)"

    ```powershell
    irm https://get.umeai.art/comfyui.ps1 | iex
    ```

=== "Linux / macOS"

    ```bash
    curl -fsSL https://get.umeai.art/comfyui.sh | sh
    ```

!!! note
    Only **Git** is required — everything else (Python, uv, dependencies) is handled automatically.

## What's Next?

- [Getting Started](getting-started.md) — Detailed installation guide
- [Architecture](architecture.md) — How the installer works
- [CLI Commands](cli-commands.md) — Full command reference
- [API Reference](api/cli.md) — Source code documentation
