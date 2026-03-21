"""
Abstract base class for platform-specific operations.

This abstraction layer enables cross-platform support by defining
a common interface for operations that differ between Windows, Linux, and macOS.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Platform(ABC):
    """Abstract base class for platform-specific operations."""

    @abstractmethod
    def create_link(self, source: Path, target: Path) -> None:
        """
        Create a directory link (junction on Windows, symlink on Unix).

        Args:
            source: The link path to create (inside ComfyUI).
            target: The target path (external folder).
        """
        ...

    @abstractmethod
    def is_admin(self) -> bool:
        """Check if the current process has administrator/root privileges."""
        ...

    @abstractmethod
    def enable_long_paths(self) -> bool:
        """
        Enable support for long file paths (>260 chars).

        Returns:
            True if long paths were enabled or already enabled.
        """
        ...

    @abstractmethod
    def detect_python(self, version: str = "3.13") -> Path | None:
        """
        Detect a specific Python version on the system.

        Args:
            version: The Python version to look for (e.g. "3.13").

        Returns:
            Path to the Python executable, or None if not found.
        """
        ...

    @abstractmethod
    def get_app_data_dir(self) -> Path:
        """Get the platform-specific application data directory."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name (e.g. 'windows', 'linux', 'macos')."""
        ...

    def is_link(self, path: Path) -> bool:
        """Check if a path is a link (junction or symlink)."""
        import os
        if path.is_symlink():
            return True
        if not path.exists():
            return False

        # Path.is_junction() is Python 3.12+
        if hasattr(path, "is_junction"):
            return path.is_junction()
        # Fallback to os.path for Python 3.11
        if hasattr(os.path, "isjunction"):
            return os.path.isjunction(str(path))

        return False


def get_platform() -> Platform:
    """
    Detect and return the appropriate Platform implementation.

    Returns:
        A Platform instance for the current OS.

    Raises:
        NotImplementedError: If the current OS is not supported.
    """
    if sys.platform == "win32":
        from src.platform.windows import WindowsPlatform

        return WindowsPlatform()
    elif sys.platform == "linux":
        from src.platform.linux import LinuxPlatform

        return LinuxPlatform()
    elif sys.platform == "darwin":
        from src.platform.macos import MacOSPlatform

        return MacOSPlatform()
    else:
        raise NotImplementedError(f"Platform '{sys.platform}' is not supported.")
