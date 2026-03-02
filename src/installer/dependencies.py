"""
Python dependency management — Steps 7-9.

Installs all Python packages required by ComfyUI:

- **Core** (Step 7): pip upgrade, PyTorch with CUDA index, ComfyUI
  ``requirements.txt``.
- **Standard + Wheels** (Step 8): additional pip packages and
  pre-built ``.whl`` files (e.g. Nunchaku, InsightFace).
- **Custom Nodes** (Step 9): delegates to :mod:`src.installer.nodes`
  for Git-clone-based node installation.
"""

from __future__ import annotations

from pathlib import Path

from src.config import DependenciesConfig
from src.utils.commands import run_and_log
from src.utils.download import download_file
from src.utils.logging import InstallerLogger


def install_core_dependencies(
    python_exe: Path,
    comfy_path: Path,
    deps: DependenciesConfig,
    log: InstallerLogger,
) -> None:
    """Install pip, PyTorch, and ComfyUI requirements.

    Performs three sub-steps:

    1. Upgrade pip and wheel.
    2. Install PyTorch packages from the CUDA index URL.
    3. Install ComfyUI's own ``requirements.txt``.

    Args:
        python_exe: Path to the venv Python executable.
        comfy_path: ComfyUI repository directory.
        deps: Parsed ``dependencies.json``.
        log: Installer logger for user-facing messages.
    """

    # Upgrade pip and wheel
    upgrade_pkgs = " ".join(deps.pip_packages.upgrade)
    log.item(f"Upgrading {upgrade_pkgs}...")
    run_and_log(
        str(python_exe),
        ["-m", "pip", "install", "--upgrade"] + deps.pip_packages.upgrade,
    )

    # PyTorch
    torch_pkgs = deps.pip_packages.torch.packages.split()
    log.item(f"Installing PyTorch ({', '.join(torch_pkgs)})...")
    run_and_log(
        str(python_exe),
        ["-m", "pip", "install"] + torch_pkgs
        + ["--index-url", deps.pip_packages.torch.index_url],
    )

    # ComfyUI requirements
    req_file = comfy_path / deps.pip_packages.comfyui_requirements
    if req_file.exists():
        log.item("Installing ComfyUI requirements...")
        run_and_log(str(python_exe), ["-m", "pip", "install", "-r", str(req_file)])


def install_python_packages(
    python_exe: Path,
    deps: DependenciesConfig,
    log: InstallerLogger,
) -> None:
    """Install additional standard pip packages listed in *deps*.

    Args:
        python_exe: Path to the venv Python executable.
        deps: Parsed ``dependencies.json``.
        log: Installer logger for user-facing messages.
    """

    if deps.pip_packages.standard:
        log.item(f"Installing {len(deps.pip_packages.standard)} standard packages...")
        run_and_log(
            str(python_exe),
            ["-m", "pip", "install"] + deps.pip_packages.standard,
        )


def install_wheels(
    python_exe: Path,
    install_path: Path,
    deps: DependenciesConfig,
    log: InstallerLogger,
) -> None:
    """Download and install pre-built ``.whl`` packages.

    Each wheel is downloaded to ``scripts/``, installed via pip,
    then deleted to save disk space.

    Args:
        python_exe: Path to the venv Python executable.
        install_path: Root installation directory.
        deps: Parsed ``dependencies.json``.
        log: Installer logger for user-facing messages.
    """
    if not deps.pip_packages.wheels:
        return

    log.item(f"Installing {len(deps.pip_packages.wheels)} wheel packages...")
    scripts_dir = install_path / "scripts"

    for wheel in deps.pip_packages.wheels:
        wheel_path = scripts_dir / f"{wheel.name}.whl"
        log.sub(f"Installing {wheel.name}...")

        try:
            download_file(wheel.url, wheel_path)
            run_and_log(str(python_exe), ["-m", "pip", "install", str(wheel_path)], ignore_errors=True)
        except Exception as e:
            log.warning(f"Failed to install {wheel.name}: {e}", level=3)
        finally:
            wheel_path.unlink(missing_ok=True)


def install_custom_nodes(
    python_exe: Path,
    comfy_path: Path,
    install_path: Path,
    log: InstallerLogger,
) -> None:
    """Install custom nodes from ``custom_nodes.json`` (additive-only).

    Resolves the manifest from ``install_path/scripts/`` or from the
    source scripts directory if not found locally. Delegates the actual
    clone + requirements install to :func:`nodes.install_all_nodes`.

    Also provisions ``nunchaku_versions.json`` into the Nunchaku node
    directory if both files exist.

    Args:
        python_exe: Path to the venv Python executable.
        comfy_path: ComfyUI repository directory.
        install_path: Root installation directory.
        log: Installer logger for user-facing messages.
    """
    from src.installer.nodes import install_all_nodes, load_manifest
    from src.installer.environment import find_source_scripts

    scripts_dir = install_path / "scripts"
    custom_nodes_dir = comfy_path / "custom_nodes"

    # Try to load manifest: install_path/scripts/ first, then source scripts
    manifest_path = scripts_dir / "custom_nodes.json"
    if not manifest_path.exists():
        source_dir = find_source_scripts()
        if source_dir:
            manifest_path = source_dir / "custom_nodes.json"

    if not manifest_path.exists():
        log.warning("custom_nodes.json not found. Skipping node installation.", level=1)
        return

    manifest = load_manifest(manifest_path)
    install_all_nodes(manifest, custom_nodes_dir, python_exe, log)

    # Copy nunchaku_versions.json into the nunchaku node directory
    # (the node expects it in its own folder, not in scripts/)
    nunchaku_src = scripts_dir / "nunchaku_versions.json"
    if not nunchaku_src.exists():
        source_dir = find_source_scripts()
        if source_dir:
            nunchaku_src = source_dir / "nunchaku_versions.json"

    nunchaku_dst = custom_nodes_dir / "ComfyUI-nunchaku" / "nunchaku_versions.json"
    if nunchaku_src.exists() and nunchaku_dst.parent.exists():
        import shutil
        shutil.copy2(nunchaku_src, nunchaku_dst)
        log.sub("  nunchaku_versions.json provisioned.", style="success")
