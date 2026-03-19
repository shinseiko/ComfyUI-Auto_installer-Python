"""Tests for the centralized UV packaging helper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.packaging import UvNotFoundError, _ensure_uv, uv_install


# ── _ensure_uv ────────────────────────────────────────────────────


class TestEnsureUv:
    """Tests for the _ensure_uv helper."""

    def test_uv_found(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/uv"):
            assert _ensure_uv() == "/usr/local/bin/uv"

    def test_uv_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            with pytest.raises(UvNotFoundError, match="uv is not installed"):
                _ensure_uv()


# ── uv_install — argument construction ────────────────────────────


class TestUvInstallArgs:
    """Verify that uv_install builds the correct command-line arguments."""

    @pytest.fixture(autouse=True)
    def _mock_uv(self) -> None:
        """Ensure uv is always 'found' during tests."""
        patcher = patch("src.utils.packaging._ensure_uv", return_value="/usr/local/bin/uv")
        patcher.start()
        yield
        patcher.stop()

    @pytest.fixture(autouse=True)
    def _mock_logger(self) -> None:
        """Provide a no-op logger."""
        patcher = patch("src.utils.packaging.get_logger", return_value=MagicMock())
        patcher.start()
        yield
        patcher.stop()

    @patch("src.utils.packaging.run_and_log")
    def test_basic_install(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["numpy", "pillow"])

        mock_run.assert_called_once()
        args = mock_run.call_args
        cmd_args = args[0][1]  # Second positional arg = args list

        assert "pip" in cmd_args
        assert "install" in cmd_args
        assert "--python" in cmd_args
        assert str(python_exe) in cmd_args
        assert "numpy" in cmd_args
        assert "pillow" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_with_index_url(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["torch"], index_url="https://download.pytorch.org/whl/cu130")

        cmd_args = mock_run.call_args[0][1]
        assert "--index-url" in cmd_args
        assert "https://download.pytorch.org/whl/cu130" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_with_requirements(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        req_file = Path("/project/requirements.txt")
        uv_install(python_exe, requirements=req_file)

        cmd_args = mock_run.call_args[0][1]
        assert "-r" in cmd_args
        assert str(req_file) in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_editable_install(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        project_root = Path("/project")
        uv_install(python_exe, editable=project_root)

        cmd_args = mock_run.call_args[0][1]
        assert "-e" in cmd_args
        assert str(project_root) in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_upgrade_flag(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["numpy"], upgrade=True)

        cmd_args = mock_run.call_args[0][1]
        assert "--upgrade" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_no_build_isolation_flag(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["sageattention"], no_build_isolation=True)

        cmd_args = mock_run.call_args[0][1]
        assert "--no-build-isolation" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_no_deps_flag(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["sageattention"], no_deps=True)

        cmd_args = mock_run.call_args[0][1]
        assert "--no-deps" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_combined_flags(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(
            python_exe,
            ["sageattention"],
            no_build_isolation=True,
            no_deps=True,
            upgrade=True,
        )

        cmd_args = mock_run.call_args[0][1]
        assert "--no-build-isolation" in cmd_args
        assert "--no-deps" in cmd_args
        assert "--upgrade" in cmd_args

    @patch("src.utils.packaging.run_and_log")
    def test_ignore_errors_forwarded(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["numpy"], ignore_errors=True)

        call_kwargs = mock_run.call_args[1]  # keyword args
        assert call_kwargs["ignore_errors"] is True

    @patch("src.utils.packaging.run_and_log")
    def test_timeout_forwarded(self, mock_run: MagicMock) -> None:
        python_exe = Path("/venv/bin/python")
        uv_install(python_exe, ["numpy"], timeout=120)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 120

    def test_uv_not_found_raises(self) -> None:
        """When uv is truly missing, uv_install must raise."""
        with patch("src.utils.packaging._ensure_uv", side_effect=UvNotFoundError("missing")):
            with pytest.raises(UvNotFoundError):
                uv_install(Path("/venv/bin/python"), ["numpy"])
