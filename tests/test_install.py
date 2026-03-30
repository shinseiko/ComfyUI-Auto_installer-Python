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

    def test_fresh_marker_detected(self, tmp_path: Path) -> None:
        """When a fresh marker exists, warnings are shown."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("fresh", encoding="utf-8")
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=False):
            _handle_partial_install(tmp_path, marker, log)

        assert log.warning.call_count >= 1
        # Marker should be removed when user declines cleanup
        assert not marker.exists()

    def test_legacy_started_marker_treated_as_fresh(self, tmp_path: Path) -> None:
        """Old-style 'started' markers are treated as fresh context."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("started", encoding="utf-8")
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=False):
            _handle_partial_install(tmp_path, marker, log)

        assert log.warning.call_count >= 1
        assert not marker.exists()

    def test_cleanup_removes_files(self, tmp_path: Path) -> None:
        """When user accepts cleanup on fresh install, partial files are removed."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("fresh", encoding="utf-8")
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
        marker.write_text("fresh", encoding="utf-8")
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
        marker.write_text("fresh", encoding="utf-8")
        (tmp_path / "ComfyUI").mkdir()
        log = MagicMock()

        with patch("src.installer.install.confirm", return_value=False):
            _handle_partial_install(tmp_path, marker, log)

        # Files should be untouched
        assert (tmp_path / "ComfyUI").exists()
        assert not marker.exists()

    # ── Migration context tests ───────────────────────────────────

    def test_migration_marker_preserves_user_data(self, tmp_path: Path) -> None:
        """Migration context preserves models, output, custom_nodes, user."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("migration", encoding="utf-8")

        # Create user data directories
        (tmp_path / "models" / "checkpoints").mkdir(parents=True)
        (tmp_path / "models" / "checkpoints" / "model.safetensors").write_text("data")
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "image.png").write_text("png")
        (tmp_path / "custom_nodes" / "MyNode").mkdir(parents=True)
        (tmp_path / "user").mkdir()

        # Create infrastructure
        (tmp_path / "ComfyUI").mkdir()
        (tmp_path / "scripts" / "venv" / "Scripts").mkdir(parents=True)

        log = MagicMock()
        _handle_partial_install(tmp_path, marker, log)

        # User data preserved
        assert (tmp_path / "models" / "checkpoints" / "model.safetensors").exists()
        assert (tmp_path / "output" / "image.png").exists()
        assert (tmp_path / "custom_nodes" / "MyNode").exists()
        assert (tmp_path / "user").exists()

        # Infrastructure cleaned
        assert not (tmp_path / "ComfyUI").exists()
        assert not (tmp_path / "scripts" / "venv").exists()

        # Marker removed
        assert not marker.exists()

    def test_migration_marker_no_prompt(self, tmp_path: Path) -> None:
        """Migration context auto-cleans without asking the user."""
        marker = tmp_path / ".install_in_progress"
        marker.write_text("migration", encoding="utf-8")
        log = MagicMock()

        # Should NOT call confirm — cleanup is automatic for migration
        with patch("src.installer.install.confirm") as mock_confirm:
            _handle_partial_install(tmp_path, marker, log)
            mock_confirm.assert_not_called()
