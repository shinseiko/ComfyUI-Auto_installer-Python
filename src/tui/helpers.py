"""Shared helpers for TUI screens.

Provides reusable utilities that multiple TUI screens depend on,
avoiding code duplication across screen modules.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def detect_vram() -> float | None:
    """Detect GPU VRAM in GiB.

    Returns:
        VRAM in GiB, or ``None`` if no GPU is detected.
    """
    try:
        from src.utils.gpu import get_gpu_vram_info
        gpu = get_gpu_vram_info()
        if gpu:
            return gpu.vram_gib
    except Exception:
        pass
    return None


def get_venv_python(install_path: Path) -> Path | None:
    """Find the ComfyUI venv Python executable.

    Searches the standard venv location at
    ``install_path/scripts/venv/``, with platform-appropriate
    binary path (``Scripts/python.exe`` on Windows,
    ``bin/python`` elsewhere).

    Args:
        install_path: Root installation directory.

    Returns:
        Path to the Python executable, or ``None`` if not found.
    """
    if sys.platform == "win32":
        venv_python = install_path / "scripts" / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = install_path / "scripts" / "venv" / "bin" / "python"
    return venv_python if venv_python.exists() else None
