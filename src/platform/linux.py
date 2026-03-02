"""
Linux-specific platform implementation.

Handles symlinks, Python detection, and admin checks on Linux systems.
Long path support is a no-op (Linux has no 260-char limit).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from src.platform.base import Platform
from src.utils.logging import get_logger


class LinuxPlatform(Platform):
    """Linux platform implementation."""

    @property
    def name(self) -> str:
        return "linux"

    def create_link(self, source: Path, target: Path) -> None:
        """
        Create a symbolic link.

        Args:
            source: The symlink path to create (inside ComfyUI).
            target: The target directory (external folder).

        Raises:
            RuntimeError: If symlink creation fails.
        """
        log = get_logger()

        if source.exists():
            if self.is_link(source):
                log.info(f"Symlink already exists: {source.name}")
                return
            else:
                raise RuntimeError(
                    f"Cannot create symlink: '{source}' already exists and is not a symlink. "
                    "Please remove it manually."
                )

        try:
            os.symlink(str(target), str(source))
        except OSError as e:
            raise RuntimeError(f"Failed to create symlink '{source}' → '{target}': {e}") from e

        if not source.exists():
            raise RuntimeError(f"Symlink creation returned success but '{source}' does not exist.")

        log.sub(f"Linked {source.name} → {target.name} (External)", style="cyan")

    def is_admin(self) -> bool:
        """Check if running as root."""
        return os.getuid() == 0

    def enable_long_paths(self) -> bool:
        """No-op on Linux — long paths are always supported."""
        log = get_logger()
        log.sub("Long path support: native (no action needed).", style="success")
        return True

    def detect_python(self, version: str = "3.13") -> Path | None:
        """
        Detect a specific Python version on Linux.

        Checks: python3.13, python3, python in PATH.

        Args:
            version: The version to look for (e.g. "3.13").

        Returns:
            Path to python executable, or None.
        """
        log = get_logger()

        # 1. Try version-specific binary (e.g. python3.13)
        versioned = shutil.which(f"python{version}")
        if versioned:
            log.sub(f"Python {version} found: {versioned}", style="success")
            return Path(versioned)

        # 2. Try python3 and check version
        for candidate_name in ("python3", "python"):
            candidate = shutil.which(candidate_name)
            if candidate:
                try:
                    result = subprocess.run(
                        [candidate, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0 and f"Python {version}" in result.stdout:
                        log.sub(f"Python {version} found: {candidate}", style="success")
                        return Path(candidate)
                except (subprocess.TimeoutExpired, OSError):
                    pass

        return None

    def get_app_data_dir(self) -> Path:
        """Get the XDG data directory (~/.local/share)."""
        xdg = os.environ.get("XDG_DATA_HOME")
        if xdg:
            return Path(xdg)
        return Path.home() / ".local" / "share"
