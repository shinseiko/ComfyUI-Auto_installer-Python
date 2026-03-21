"""Smoke tests for the CLI entry point."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove terminal color codes from testing output."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


class TestCLISmoke:
    """Verify the CLI wires up correctly without running the installer."""

    def test_help_shows_version(self) -> None:
        """--help should include the app name and show available commands."""
        result = runner.invoke(app, ["--help"], env={"NO_COLOR": "1"})
        assert result.exit_code == 0
        clean_out = strip_ansi(result.output).lower()
        assert "umeairt-comfyui-installer" in clean_out or "install" in clean_out

    def test_install_help(self) -> None:
        """install --help should show all expected options."""
        result = runner.invoke(app, ["install", "--help"], env={"NO_COLOR": "1"})
        assert result.exit_code == 0
        clean_out = strip_ansi(result.output)
        assert "--path" in clean_out
        assert "--type" in clean_out
        assert "--nodes" in clean_out
        assert "--yes" in clean_out
        assert "--verbose" in clean_out

    def test_update_help(self) -> None:
        """update --help should show all expected options."""
        result = runner.invoke(app, ["update", "--help"], env={"NO_COLOR": "1"})
        assert result.exit_code == 0
        clean_out = strip_ansi(result.output)
        assert "--path" in clean_out
        assert "--verbose" in clean_out
        assert "--yes" in clean_out

    def test_install_invalid_type(self) -> None:
        """install --type invalid should fail with a helpful error."""
        result = runner.invoke(app, ["install", "--type", "invalid"], env={"NO_COLOR": "1"})
        assert result.exit_code != 0
        clean_out = strip_ansi(result.output)
        assert "invalid" in clean_out.lower() or "Invalid" in clean_out

    def test_install_invalid_nodes(self) -> None:
        """install --nodes bogus should fail with a helpful error."""
        result = runner.invoke(app, ["install", "--nodes", "bogus"], env={"NO_COLOR": "1"})
        assert result.exit_code != 0
        clean_out = strip_ansi(result.output)
        assert "bogus" in clean_out.lower() or "Invalid" in clean_out
