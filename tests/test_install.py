"""Tests for the install orchestrator — crash detection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.installer.install import _handle_partial_install

if __import__("typing").TYPE_CHECKING:
    from pathlib import Path


class TestHandlePartialInstall:
    """Tests for _handle_partial_install crash detection."""

    def test_no_marker_does_nothing(self, tmp_path: Path) -> None:
        """When no marker exists, nothing happens."""
        marker = tmp_path / ".install_in_progress"
        log = MagicMock()
        _handle_partial_install(tmp_path, marker, log)
        log.warning.assert_not_called()

    def test_marker_detected(self, tmp_path: Path) -> None:
        """When marker exists, a warning is shown."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("started", encoding="utf-8")
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=False):
            _handle_partial_install(tmp_path, marker, log)

        log.warning.assert_called_once()
        # Marker should be removed when user declines cleanup
        assert not marker.exists()

    def test_cleanup_removes_files(self, tmp_path: Path) -> None:
        """When user accepts cleanup, partial files are removed."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("started", encoding="utf-8")
        (tmp_path / "ComfyUI").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "some_config.json").write_text("{}")
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=True):
            _handle_partial_install(tmp_path, marker, log)

        # Partial install should be cleaned
        assert not (tmp_path / "ComfyUI").exists()
        assert not (tmp_path / "scripts").exists()

    def test_cleanup_preserves_logs(self, tmp_path: Path) -> None:
        """Cleanup should preserve the logs directory."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("started", encoding="utf-8")
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "install_log.txt").write_text("important log data")
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=True):
            _handle_partial_install(tmp_path, marker, log)

        # Logs should be preserved
        assert logs_dir.exists()
        assert (logs_dir / "install_log.txt").read_text() == "important log data"

    def test_decline_cleanup_keeps_files(self, tmp_path: Path) -> None:
        """When user declines, files are kept and marker is removed."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("started", encoding="utf-8")
        (tmp_path / "ComfyUI").mkdir()
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=False):
            _handle_partial_install(tmp_path, marker, log)

        # Files should be untouched
        assert (tmp_path / "ComfyUI").exists()
        assert not marker.exists()
