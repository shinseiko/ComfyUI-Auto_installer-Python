"""
System prerequisites — Steps 1-2.

Checks and installs external tools required before the Python
environment or ComfyUI can be set up:

- **Git**: version check against ``MIN_GIT_VERSION``, auto-install on Windows,
  or OS-specific upgrade instructions.
- **aria2**: 3-tier search (system PATH → local ``scripts/aria2/`` →
  download on Windows / suggest on Linux).

Typical usage::

    from src.installer.system import check_prerequisites, ensure_aria2

    if not check_prerequisites(log):
        install_git(log)
    ensure_aria2(install_path, log)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from src.utils.commands import check_command_exists
from src.utils.download import download_file
from src.utils.prompts import confirm

if TYPE_CHECKING:
    from src.utils.logging import InstallerLogger

# Minimum Git version for reliable operation (long paths, partial clone, etc.)
MIN_GIT_VERSION = (2, 39, 0)


def _parse_git_version(version_string: str) -> tuple[int, ...] | None:
    """Parse ``git version X.Y.Z...`` into a comparable tuple.

    Args:
        version_string: Raw output from ``git --version``.

    Returns:
        Tuple of ``(major, minor, patch)`` ints, or ``None`` if
        the string cannot be parsed.
    """
    match = re.search(r"(\d+\.\d+\.\d+)", version_string)
    if match:
        return tuple(int(x) for x in match.group(1).split("."))
    return None


def check_prerequisites(log: InstallerLogger) -> bool:
    """Verify that required external tools are present and up to date.

    Checks Git availability and version. If Git is outdated, offers
    OS-specific update instructions (auto-update on Windows, manual
    commands on Linux/macOS).

    Args:
        log: Installer logger for user-facing messages.

    Returns:
        ``True`` if all prerequisites are met (Git present and
        usable). ``False`` if Git is missing entirely.
    """
    all_ok = True

    # Check Git
    if check_command_exists("git"):
        git_ver_str = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
        git_ver = _parse_git_version(git_ver_str)

        if git_ver and git_ver < MIN_GIT_VERSION:
            min_str = ".".join(str(v) for v in MIN_GIT_VERSION)
            log.warning(f"Git {git_ver_str} is outdated (minimum: {min_str}).", level=2)

            if sys.platform == "win32":
                if confirm("Would you like to update Git now?"):
                    # Running the Git installer again updates in-place
                    if install_git(log):
                        log.sub("Git updated successfully.", style="success")
                    else:
                        log.warning("Git update failed. Continuing with current version.", level=2)
                else:
                    log.item("Continuing with current Git version.")
            elif sys.platform == "darwin":
                log.item("Update with: brew upgrade git")
            else:
                log.item("Update with: sudo apt update && sudo apt install git")
        else:
            log.sub(f"Git: {git_ver_str}", style="success")
    else:
        log.warning("Git is not installed.", level=2)
        all_ok = False

    return all_ok


def install_git(log: InstallerLogger) -> bool:
    """Download and silently install Git for Windows.

    On non-Windows platforms, prints manual installation instructions
    and returns ``False`` immediately.

    Args:
        log: Installer logger for user-facing messages.

    Returns:
        ``True`` if Git was installed successfully, ``False`` otherwise.
    """
    if sys.platform != "win32":
        log.error("Automatic Git installation is only supported on Windows.")
        log.item("Please install Git manually: sudo apt install git (Linux) or brew install git (macOS)")
        return False

    if not confirm("Git is required. Would you like to install it automatically?"):
        log.error("Installation aborted — Git is mandatory.")
        return False

    log.item("Downloading Git for Windows...")
    git_url = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe"
    git_installer = Path(os.environ.get("TEMP", "/tmp")) / "git-installer.exe"

    try:
        download_file(git_url, git_installer)
        log.sub("Installing Git (accept UAC if prompted)...")

        result = subprocess.run(
            [str(git_installer), "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-",
             "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"],
            timeout=300,
        )

        if result.returncode == 0:
            log.success("Git installed successfully.", level=2)
            # Refresh PATH
            if sys.platform == "win32":
                os.environ["PATH"] = (
                    os.environ.get("PATH", "")
                    + ";"
                    + r"C:\Program Files\Git\cmd"
                )
            return True
        else:
            log.error(f"Git installer failed with code {result.returncode}.")
            return False
    except Exception as e:
        log.error(f"Git installation failed: {e}")
        return False
    finally:
        git_installer.unlink(missing_ok=True)


def ensure_aria2(install_path: Path, log: InstallerLogger) -> bool:
    """Ensure the aria2 download accelerator is available.

    Uses a 3-tier search strategy:

    1. System ``PATH`` (user or package-manager installed).
    2. ``install_path/scripts/aria2/`` (downloaded by a previous run).
    3. **Windows**: download and extract to ``scripts/aria2/``.
       **Linux/macOS**: suggest package manager installation.

    If found in tier 2 or 3, the directory is prepended to
    ``os.environ["PATH"]`` so subsequent calls can find ``aria2c``.

    Args:
        install_path: Root installation directory.
        log: Installer logger for user-facing messages.

    Returns:
        ``True`` if aria2 is available after this call.
    """
    # 1. Check system PATH
    if check_command_exists("aria2c"):
        log.sub("aria2 found in system PATH.", style="success")
        return True

    # 2. Check install_path/scripts/aria2/
    exe_name = "aria2c.exe" if sys.platform == "win32" else "aria2c"
    local_aria2 = install_path / "scripts" / "aria2" / exe_name
    if local_aria2.exists():
        os.environ["PATH"] = str(local_aria2.parent) + os.pathsep + os.environ.get("PATH", "")
        log.sub("aria2 found in scripts/aria2/.", style="success")
        return True

    # 3. Platform-specific: download or suggest
    if sys.platform == "win32":
        return _download_aria2_windows(install_path, log)
    else:
        log.info("aria2 is not installed. Downloads will use standard speed.")
        if sys.platform == "darwin":
            log.item("Install with: brew install aria2")
        else:
            log.item("Install with: sudo apt install aria2  (or your package manager)")
        return False


def _download_aria2_windows(install_path: Path, log: InstallerLogger) -> bool:
    """Download and extract aria2 for Windows.

    The archive is downloaded to ``%TEMP%``, extracted into
    ``install_path/scripts/aria2/``, and the executable is
    moved to the root of that directory.

    Args:
        install_path: Root installation directory.
        log: Installer logger for user-facing messages.

    Returns:
        ``True`` if ``aria2c.exe`` is available after extraction.
    """
    log.item("Downloading aria2 (download accelerator)...")
    aria2_url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    aria2_dir = install_path / "scripts" / "aria2"
    aria2_exe = aria2_dir / "aria2c.exe"

    zip_path = Path(os.environ.get("TEMP", ".")) / "aria2.zip"
    try:
        download_file(aria2_url, zip_path)
        log.sub("Extracting aria2...")
        aria2_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(aria2_dir)

        # Find aria2c.exe in extracted contents (may be in a subdirectory)
        for root, _dirs, files in os.walk(aria2_dir):
            for f in files:
                if f.lower() == "aria2c.exe":
                    src = Path(root) / f
                    if src.parent != aria2_dir:
                        shutil.move(str(src), str(aria2_exe))
                    break

        if aria2_exe.exists():
            os.environ["PATH"] = str(aria2_dir) + ";" + os.environ.get("PATH", "")
            log.sub("aria2 installed to scripts/aria2/.", style="success")
            return True

        log.warning("aria2c.exe not found in archive.", level=2)
        return False

    except Exception as e:
        log.warning(f"aria2 download failed: {e}. Downloads will use standard speed.", level=2)
        return False
    finally:
        zip_path.unlink(missing_ok=True)
