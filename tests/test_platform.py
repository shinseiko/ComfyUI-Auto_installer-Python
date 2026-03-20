"""Tests for the platform abstraction layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.platform.base import Platform, get_platform


class TestGetPlatform:
    """Tests for the get_platform factory."""

    def test_returns_platform_instance(self) -> None:
        """Should return a Platform subclass for the current OS."""
        platform = get_platform()
        assert isinstance(platform, Platform)

    def test_windows_returns_windows_platform(self) -> None:
        """On win32, should return WindowsPlatform."""
        with patch("src.platform.base.sys") as mock_sys:
            mock_sys.platform = "win32"
            platform = get_platform()
            assert platform.name == "windows"

    def test_linux_returns_linux_platform(self) -> None:
        """On linux, should return LinuxPlatform."""
        with patch("src.platform.base.sys") as mock_sys:
            mock_sys.platform = "linux"
            platform = get_platform()
            assert platform.name == "linux"

    def test_unsupported_raises(self) -> None:
        """Should raise NotImplementedError for unknown platforms."""
        with (
            patch("src.platform.base.sys") as mock_sys,
            pytest.raises(NotImplementedError, match="not supported"),
        ):
            mock_sys.platform = "aix"
            get_platform()


class TestIsLink:
    """Tests for the base is_link method."""

    def test_regular_dir_is_not_link(self, tmp_path: Path) -> None:
        """A regular directory should not be detected as a link."""
        d = tmp_path / "regular"
        d.mkdir()
        platform = get_platform()
        assert platform.is_link(d) is False

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """A path that doesn't exist should not be a link."""
        platform = get_platform()
        assert platform.is_link(tmp_path / "no_exist") is False


class TestPlatformProperties:
    """Tests for platform properties."""

    def test_name_is_string(self) -> None:
        """Platform name should be a non-empty string."""
        platform = get_platform()
        assert isinstance(platform.name, str)
        assert len(platform.name) > 0

    def test_detect_python_returns_path_or_none(self) -> None:
        """detect_python should return Path or None."""
        platform = get_platform()
        result = platform.detect_python("3.13")
        assert result is None or isinstance(result, Path)
