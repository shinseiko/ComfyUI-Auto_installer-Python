"""
Performance optimizations — Step 10.

Installs GPU acceleration libraries:

- **Triton**: ``triton-windows`` on Windows, ``triton`` on Linux.
  Version is constrained to match the installed PyTorch build.
- **SageAttention**: installed with ``--no-build-isolation``;
  retried without deps if the first attempt fails.

Skipped entirely if no NVIDIA GPU is detected.

Credit:
    Logic inspired by `DazzleML's comfyui-triton-sageattention installer
    <https://github.com/DazzleML/comfyui-triton-and-sageattention-installer>`_.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src.config import DependenciesConfig
from src.utils.commands import CommandError, run_and_log
from src.utils.gpu import detect_nvidia_gpu
from src.utils.logging import InstallerLogger


def _check_package_installed(python_exe: Path, package: str) -> str | None:
    """Check whether a pip package is installed.

    Args:
        python_exe: Path to the venv Python executable.
        package: Package name to check (e.g. ``"triton"``).

    Returns:
        Installed version string, or ``None`` if not installed.
    """
    result = subprocess.run(
        [str(python_exe), "-c",
         f"from importlib.metadata import version; print(version('{package}'))"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _get_cuda_version_from_torch(python_exe: Path) -> str | None:
    """Detect CUDA version from the installed PyTorch build.

    Args:
        python_exe: Path to the venv Python executable.

    Returns:
        CUDA version string (e.g. ``"12.8"``), or ``None``.
    """
    result = subprocess.run(
        [str(python_exe), "-c",
         "import torch; print(torch.version.cuda or '')"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        ver = result.stdout.strip()
        return ver if ver else None
    return None


def _get_torch_version(python_exe: Path) -> str | None:
    """Get the installed PyTorch version string.

    Args:
        python_exe: Path to the venv Python executable.

    Returns:
        Version string (e.g. ``"2.8.0+cu128"``), or ``None``.
    """
    result = subprocess.run(
        [str(python_exe), "-c", "import torch; print(torch.__version__)"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _get_triton_constraint(torch_ver: str) -> str:
    """Map a PyTorch version to a compatible ``triton-windows`` version range.

    Based on the `triton-windows compatibility matrix
    <https://github.com/woct0rdho/triton-windows/issues/158>`_.

    Args:
        torch_ver: PyTorch version string (e.g. ``"2.8.0+cu128"``).

    Returns:
        PEP 440 version specifier (e.g. ``">=3.4,<3.5"``), or an
        empty string if the version cannot be parsed.
    """
    try:
        parts = torch_ver.split(".")
        major = int(parts[0])
        minor = int(parts[1].split("+")[0])  # Handle "+cu128" suffix

        if (major, minor) >= (2, 9):
            return ">=3.5,<4"
        elif (major, minor) >= (2, 8):
            return ">=3.4,<3.5"
        elif (major, minor) >= (2, 7):
            return ">=3.3,<3.4"
        elif (major, minor) >= (2, 6):
            return ">=3.2,<3.3"
        else:
            return "<3.2"
    except (ValueError, IndexError):
        return ""  # No constraint if can't parse


def install_optimizations(
    python_exe: Path,
    comfy_path: Path,
    install_path: Path,
    deps: DependenciesConfig,
    log: InstallerLogger,
) -> None:
    """Install Triton and SageAttention for GPU inference acceleration.

    Skipped if no NVIDIA GPU is detected. Triton version is
    constrained to match the installed PyTorch build.
    SageAttention is retried without deps on first failure.

    Args:
        python_exe: Path to the venv Python executable.
        comfy_path: ComfyUI repository directory.
        install_path: Root installation directory.
        deps: Parsed ``dependencies.json``.
        log: Installer logger for user-facing messages.
    """
    if not detect_nvidia_gpu():
        log.info("No NVIDIA GPU — skipping Triton/SageAttention.")
        return

    log.item("Installing Triton and SageAttention...")

    # Set CUDA_HOME if available
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        os.environ["CUDA_HOME"] = cuda_path

    # Detect CUDA and torch version
    cuda_ver = _get_cuda_version_from_torch(python_exe)
    if cuda_ver:
        log.sub(f"CUDA {cuda_ver} detected from torch.", style="success")
    else:
        log.warning("Could not detect CUDA from torch. Triton may not work.", level=2)

    # --- Triton ---
    base_package = "triton-windows" if sys.platform == "win32" else "triton"
    triton_ver = _check_package_installed(python_exe, base_package)
    if triton_ver is None and base_package == "triton-windows":
        triton_ver = _check_package_installed(python_exe, "triton")

    if triton_ver:
        log.sub(f"Triton already installed: v{triton_ver}", style="success")
    else:
        # Determine version constraint from PyTorch
        torch_ver = _get_torch_version(python_exe)
        constraint = _get_triton_constraint(torch_ver) if torch_ver else ""
        package_spec = f"{base_package}{constraint}" if constraint else base_package

        if constraint:
            log.sub(f"PyTorch {torch_ver} → Triton constraint: {constraint}")

        log.sub(f"Installing {package_spec}...")
        try:
            run_and_log(
                str(python_exe),
                ["-m", "pip", "install", package_spec,
                 "--no-warn-script-location"],
                ignore_errors=True,
                timeout=300,
            )
        except CommandError:
            log.warning(f"{base_package} install failed.", level=2)

        # Verify
        triton_ver = _check_package_installed(python_exe, base_package)
        if triton_ver is None and base_package == "triton-windows":
            triton_ver = _check_package_installed(python_exe, "triton")

        if triton_ver:
            log.sub(f"Triton installed: v{triton_ver}", style="success")
        else:
            log.warning("Triton could not be installed. SageAttention may be limited.", level=2)

    # --- SageAttention ---
    sage_ver = _check_package_installed(python_exe, "sageattention")

    if sage_ver:
        log.sub(f"SageAttention already installed: v{sage_ver}", style="success")
    else:
        log.sub("Installing SageAttention...")
        try:
            run_and_log(
                str(python_exe),
                ["-m", "pip", "install", "sageattention",
                 "--no-warn-script-location", "--no-build-isolation"],
                timeout=300,
            )
        except CommandError:
            # Retry without deps (common workaround)
            log.sub("Retrying SageAttention without deps...", style="yellow")
            run_and_log(
                str(python_exe),
                ["-m", "pip", "install", "sageattention",
                 "--no-deps", "--no-warn-script-location",
                 "--no-build-isolation"],
                ignore_errors=True,
                timeout=300,
            )

        sage_ver = _check_package_installed(python_exe, "sageattention")
        if sage_ver:
            log.sub(f"SageAttention installed: v{sage_ver}", style="success")
        else:
            log.warning("SageAttention could not be installed.", level=2)
