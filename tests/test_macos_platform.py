"""Tests for the macOS platform abstraction."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.skipif(os.name == "nt", reason="macOS platform tests")


class TestMacOSPlatform:
    """Tests for the MacOSPlatform implementation."""

    def setup_method(self) -> None:
        from src.platform.macos import MacOSPlatform

        self.platform = MacOSPlatform()

    def test_name(self) -> None:
        assert self.platform.name == "macos"

    def test_is_admin_true(self) -> None:
        with patch("os.getuid", return_value=0):
            assert self.platform.is_admin() is True

    def test_is_admin_false(self) -> None:
        with patch("os.getuid", return_value=1000):
            assert self.platform.is_admin() is False

    def test_enable_long_paths_noop(self) -> None:
        """macOS natively supports long paths; should always return True."""
        assert self.platform.enable_long_paths() is True

    def test_get_app_data_dir(self) -> None:
        """Should point to ~/Library/Application Support/UmeAiRT."""
        app_data = self.platform.get_app_data_dir()
        assert app_data.name == "UmeAiRT"
        assert app_data.parent.name == "Application Support"
        assert app_data.parent.parent.name == "Library"

    def test_create_link_success(self, tmp_path: Path) -> None:
        """create_link should use os.symlink."""
        source = tmp_path / "link"
        target = tmp_path / "target"
        target.mkdir()

        self.platform.create_link(source, target)

        assert source.exists()
        assert source.is_symlink()
        assert source.resolve() == target.resolve()

    def test_create_link_already_exists(self, tmp_path: Path) -> None:
        """create_link should do nothing if symlink already points to target (or exists)."""
        source = tmp_path / "link"
        target = tmp_path / "target"
        target.mkdir()

        os.symlink(target, source)
        # Second call should not crash
        self.platform.create_link(source, target)

    def test_create_link_conflict(self, tmp_path: Path) -> None:
        """create_link should raise RuntimeError if source is a normal dir/file."""
        source = tmp_path / "link"
        target = tmp_path / "target"
        target.mkdir()
        source.mkdir()  # It's a real directory, not a symlink

        with pytest.raises(RuntimeError, match="already exists and is not a symlink"):
            self.platform.create_link(source, target)

    @patch("shutil.which")
    def test_detect_python_versioned_binary(self, mock_which) -> None:
        """detect_python should find 'python3.13' directly via shutil.which."""
        mock_which.return_value = "/usr/local/bin/python3.13"

        # Mock out homebrew checks so they fail
        with patch("os.access", return_value=False), patch("pathlib.Path.exists", return_value=False):
            result = self.platform.detect_python("3.13")

        mock_which.assert_called_once_with("python3.13")
        assert result == Path("/usr/local/bin/python3.13")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_detect_python_fallback(self, mock_run, mock_which) -> None:
        """detect_python should fall back to testing 'python3' binary output."""
        def which_side_effect(name: str):
            if name == "python3.13":
                return None
            if name == "python3":
                return "/usr/bin/python3"
            return None
        mock_which.side_effect = which_side_effect

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Python 3.13.2"
        )

        with patch("os.access", return_value=False), patch("pathlib.Path.exists", return_value=False):
            result = self.platform.detect_python("3.13")

        assert result == Path("/usr/bin/python3")
