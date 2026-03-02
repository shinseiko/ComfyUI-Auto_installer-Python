"""
Python environment and configuration provisioning — Steps 3-4.

Creates the Python virtual environment and copies the minimum
configuration files needed for the rest of the install:

- **venv creation** (Step 3): tries ``uv`` first (auto-downloads
  Python 3.13), falls back to system Python.
- **Provisioning** (Step 4): copies ``dependencies.json`` and the
  model catalog to the install directory.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.platform.base import get_platform
from src.utils.commands import CommandError, check_command_exists, run_and_log
from src.utils.download import download_file
from src.utils.logging import InstallerLogger
from src.utils.prompts import confirm


def setup_environment(
    install_path: Path,
    install_type: str,
    log: InstallerLogger,
) -> Path:
    """Create the Python virtual environment.

    Strategy (in order):

    1. ``uv venv`` with Python 3.13 auto-managed.
    2. Local ``uv`` binary from bootstrap (``scripts/uv/``).
    3. System Python 3.13 (detected via platform abstraction).
    4. Auto-install Python 3.13 on Windows (if user agrees).

    After creation, verifies the expected ``python`` executable
    exists inside the venv.

    Args:
        install_path: Root installation directory.
        install_type: ``"venv"`` or ``"conda"`` (conda not yet implemented).
        log: Installer logger for user-facing messages.

    Returns:
        Absolute path to the Python executable inside the environment.

    Raises:
        SystemExit: If no usable Python 3.13 can be found or created.
    """
    scripts_dir = install_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    log.item(f"Install path: {install_path}")

    if install_type == "venv":
        venv_path = scripts_dir / "venv"

        if venv_path.exists():
            log.sub("Virtual environment already exists.", style="success")
        else:
            # Try uv first — it handles Python download automatically
            if check_command_exists("uv"):
                log.item("Creating venv with uv (Python 3.13 auto-managed)...")
                try:
                    run_and_log("uv", ["venv", str(venv_path), "--python", "3.13", "--seed"])
                    log.sub("Virtual environment created via uv.", style="success")
                except CommandError:
                    log.warning("uv venv creation failed, falling back to system Python.", level=2)
                    venv_path_exists = False
                else:
                    venv_path_exists = True
            else:
                # Also check for uv in scripts/uv/ (installed by bootstrap)
                local_uv = scripts_dir / "uv" / ("uv.exe" if sys.platform == "win32" else "uv")
                if local_uv.exists():
                    log.item("Creating venv with local uv (Python 3.13 auto-managed)...")
                    try:
                        run_and_log(str(local_uv), ["venv", str(venv_path), "--python", "3.13", "--seed"])
                        log.sub("Virtual environment created via uv.", style="success")
                    except CommandError:
                        log.warning("uv venv creation failed, falling back to system Python.", level=2)
                        venv_path_exists = False
                    else:
                        venv_path_exists = True
                else:
                    venv_path_exists = False

            # Fallback: use system Python if uv didn't create the venv
            if not venv_path.exists():
                platform = get_platform()
                python_path = platform.detect_python("3.13")

                if python_path is None:
                    # Try to install Python 3.13 (no fallback — wheels are cp313 only)
                    if sys.platform == "win32" and confirm("Python 3.13 not found. Install automatically?"):
                        python_path = _install_python_windows(log)

                    if python_path is None:
                        log.error("Python 3.13 is required (wheels are compiled for cp313).")
                        log.item("Please install from https://www.python.org/downloads/release/python-31311/")
                        raise SystemExit(1)

                log.item(f"Creating venv with {python_path}...")
                run_and_log(str(python_path), ["-m", "venv", str(venv_path)])
                log.sub("Virtual environment created.", style="success")

        # Return the venv python and verify it exists
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"

        if not python_exe.exists():
            log.error(f"Venv python not found at expected path: {python_exe}")
            log.item(f"Venv directory: {venv_path}")
            raise SystemExit(1)

        log.sub(f"Venv python: {python_exe}", style="success")
        return python_exe

    else:
        log.warning("Conda support is planned but not yet implemented in the Python version.")
        log.item("Please use --type venv for now.")
        raise SystemExit(1)


def _install_python_windows(log: InstallerLogger) -> Path | None:
    """Download and install Python 3.13 on Windows.

    Uses the official Python installer in ``/passive`` mode.
    After installation, searches well-known paths and the ``py``
    launcher to locate the new executable.

    Args:
        log: Installer logger for user-facing messages.

    Returns:
        Path to the installed ``python.exe``, or ``None`` on failure.
    """
    py_url = "https://www.python.org/ftp/python/3.13.11/python-3.13.11-amd64.exe"
    py_installer = Path(os.environ.get("TEMP", ".")) / "python-3.13.11-amd64.exe"

    try:
        log.item("Downloading Python 3.13...")
        download_file(py_url, py_installer)

        log.sub("Installing Python (this may take a minute)...")
        result = subprocess.run(
            [str(py_installer), "/passive", "PrependPath=1",
             "Include_launcher=1", "Include_test=0"],
            timeout=300,
        )

        if result.returncode == 0:
            log.success("Python 3.13 installed.", level=2)

            # Try to find the new installation
            candidates = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python/Python313/python.exe",
                Path("C:/Program Files/Python313/python.exe"),
            ]
            for p in candidates:
                if p.exists():
                    return p

            # Try py launcher
            if check_command_exists("py"):
                try:
                    r = subprocess.run(
                        ["py", "-3.13", "-c", "import sys; print(sys.executable)"],
                        capture_output=True, text=True, timeout=10,
                    )
                    if r.returncode == 0:
                        return Path(r.stdout.strip())
                except Exception:
                    pass

        log.error("Python installation failed.")
        return None
    except Exception as e:
        log.error(f"Python installation error: {e}")
        return None
    finally:
        py_installer.unlink(missing_ok=True)


def find_source_scripts() -> Path | None:
    """Locate the source ``scripts/`` directory containing config files.

    Searches two locations:

    1. Relative to this package: ``../../scripts/`` from ``environment.py``.
    2. Relative to the current working directory: ``./scripts/``.

    Returns:
        Path to the scripts directory, or ``None`` if not found.
    """
    # 1. Relative to this file: src/installer/environment.py → ../../scripts/
    package_root = Path(__file__).resolve().parent.parent.parent
    candidate = package_root / "scripts"
    if (candidate / "dependencies.json").exists():
        return candidate

    # 2. Current working directory
    candidate = Path.cwd() / "scripts"
    if (candidate / "dependencies.json").exists():
        return candidate

    return None


# Files needed to bootstrap the install (copied early).
BOOTSTRAP_FILES = [
    "dependencies.json",
]

# Files resolved on-demand from source when needed.
DEFERRED_FILES = [
    "custom_nodes.json",
    "environment.yml",
    "nunchaku_versions.json",
]


def provision_scripts(install_path: Path, log: InstallerLogger) -> None:
    """Copy bootstrap config files to the install directory.

    Only copies files listed in ``BOOTSTRAP_FILES`` (currently just
    ``dependencies.json``). Other configs like ``custom_nodes.json``
    are resolved on-demand by later steps from the source directory.

    Also copies ``umeairt_bundles.json`` to ``install_path/scripts/``
    so the model downloader can find it.

    Args:
        install_path: Root installation directory.
        log: Installer logger for user-facing messages.
    """

    source_dir = find_source_scripts()
    if source_dir is None:
        log.warning("Could not find source scripts directory.", level=1)
        log.info("Looking for dependencies.json relative to the package and CWD.")
        return

    dest_dir = install_path / "scripts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for filename in BOOTSTRAP_FILES:
        src = source_dir / filename
        dst = dest_dir / filename

        if not src.exists():
            log.sub(f"  {filename}: [dim]not in source (skipped)[/dim]")
            continue

        if dst.exists():
            # Update if source is newer
            if src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(src, dst)
                log.sub(f"  {filename}: updated", style="cyan")
                copied += 1
            else:
                log.sub(f"  {filename}: already up to date", style="success")
        else:
            shutil.copy2(src, dst)
            log.sub(f"  {filename}: copied", style="success")
            copied += 1

    # Also copy umeairt_bundles.json to scripts/ for the model downloader
    bundles_src = source_dir / "umeairt_bundles.json"
    if not bundles_src.exists():
        bundles_src = source_dir.parent / "umeairt_bundles.json"
    bundles_dst = dest_dir / "umeairt_bundles.json"

    if bundles_src.exists():
        if not bundles_dst.exists() or bundles_src.stat().st_mtime > bundles_dst.stat().st_mtime:
            shutil.copy2(bundles_src, bundles_dst)
            log.sub("  umeairt_bundles.json: copied to scripts/", style="success")
            copied += 1

    log.item(f"{copied} file(s) provisioned.")
