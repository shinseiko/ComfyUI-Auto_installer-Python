"""Tests for the system prerequisites module."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from src.installer.system import (
    MIN_GIT_VERSION,
    _parse_git_version,
    check_prerequisites,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestParseGitVersion:
    """Tests for _parse_git_version."""

    def test_standard_format(self) -> None:
        assert _parse_git_version("git version 2.47.1.windows.1") == (2, 47, 1)

    def test_linux_format(self) -> None:
        assert _parse_git_version("git version 2.43.0") == (2, 43, 0)

    def test_short_version_no_match(self) -> None:
        """Versions without 3 parts (X.Y) are not parseable by the regex."""
        assert _parse_git_version("git version 2.40") is None

    def test_no_match(self) -> None:
        assert _parse_git_version("not a version string") is None

    def test_empty_string(self) -> None:
        assert _parse_git_version("") is None

    def test_min_git_version_is_tuple(self) -> None:
        """MIN_GIT_VERSION should be a 3-tuple of ints."""
        assert isinstance(MIN_GIT_VERSION, tuple)
        assert len(MIN_GIT_VERSION) == 3
        assert all(isinstance(v, int) for v in MIN_GIT_VERSION)


class TestCheckPrerequisites:
    """Tests for check_prerequisites (mocked)."""

    def test_git_available(self) -> None:
        """Returns True when git is found and version is ok."""
        log = MagicMock()
        mock_result = MagicMock()
        mock_result.stdout = "git version 2.47.1"
        with (
            patch("src.installer.system.check_command_exists", return_value=True),
            patch("src.installer.system.subprocess.run", return_value=mock_result),
        ):
            assert check_prerequisites(log) is True

    def test_git_missing(self) -> None:
        """Returns False when git is not found."""
        log = MagicMock()
        with patch("src.installer.system.check_command_exists", return_value=False):
            assert check_prerequisites(log) is False

    def test_git_old_version(self) -> None:
        """Returns True (with warning) when git version is old but present."""
        log = MagicMock()
        mock_result = MagicMock()
        mock_result.stdout = "git version 2.20.0"
        with (
            patch("src.installer.system.check_command_exists", return_value=True),
            patch("src.installer.system.subprocess.run", return_value=mock_result),
            patch("src.installer.system.confirm", return_value=False),  # decline update
        ):
            result = check_prerequisites(log)
            assert result is True


class TestZipSlipPrevention:
    """Test that zip extraction validates paths."""

    def test_safe_zip_extracts(self, tmp_path: Path) -> None:
        """A normal zip file should extract without issues."""
        zip_path = tmp_path / "safe.zip"
        target_dir = tmp_path / "output"
        target_dir.mkdir()

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file.txt", "safe content")
            zf.writestr("subdir/file2.txt", "also safe")

        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                target = (target_dir / member).resolve()
                assert str(target).startswith(str(target_dir.resolve()))
            zf.extractall(target_dir)

        assert (target_dir / "file.txt").exists()
        assert (target_dir / "subdir" / "file2.txt").exists()
