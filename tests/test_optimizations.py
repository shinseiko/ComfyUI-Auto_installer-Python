"""Tests for the performance optimizations module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.installer.optimizations import (
    _check_package_installed,
    _get_cuda_version_from_torch,
    _get_torch_version,
    _get_triton_constraint,
)


class TestCheckPackageInstalled:
    """Tests for _check_package_installed."""

    def test_installed(self) -> None:
        """Returns version string when package is installed."""
        mock_result = MagicMock(returncode=0, stdout="3.2.0\n")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _check_package_installed(MagicMock(), "triton") == "3.2.0"

    def test_not_installed(self) -> None:
        """Returns None when package is not installed."""
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _check_package_installed(MagicMock(), "triton") is None


class TestGetCudaVersion:
    """Tests for _get_cuda_version_from_torch."""

    def test_cuda_detected(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="12.8\n")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _get_cuda_version_from_torch(MagicMock()) == "12.8"

    def test_no_cuda(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="\n")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _get_cuda_version_from_torch(MagicMock()) is None

    def test_pytorch_not_installed(self) -> None:
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _get_cuda_version_from_torch(MagicMock()) is None


class TestGetTorchVersion:
    """Tests for _get_torch_version."""

    def test_version_detected(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="2.8.0+cu128\n")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _get_torch_version(MagicMock()) == "2.8.0+cu128"

    def test_not_installed(self) -> None:
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("src.installer.optimizations.subprocess.run", return_value=mock_result):
            assert _get_torch_version(MagicMock()) is None


class TestGetTritonConstraint:
    """Tests for _get_triton_constraint."""

    def test_torch_2_10(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("2.10.0+cu130", deps) == ">=3.5,<4"

    def test_torch_2_8(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("2.8.0+cu128", deps) == ">=3.4,<3.5"

    def test_torch_2_7(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("2.7.0+cu124", deps) == ">=3.3,<3.4"

    def test_torch_2_6(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("2.6.0+cu121", deps) == ">=3.2,<3.3"

    def test_torch_old(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("2.5.0", deps) == "<3.2"

    def test_invalid_version(self) -> None:
        deps = MagicMock(optimizations=None)
        assert _get_triton_constraint("not-a-version", deps) == ""

    def test_config_driven_constraint(self) -> None:
        """Config-driven constraints override hardcoded table."""
        deps = MagicMock()
        deps.optimizations.triton.version_constraints = {"2.10": ">=4.0,<5"}
        assert _get_triton_constraint("2.10.0+cu130", deps) == ">=4.0,<5"


class TestInstallOptimizations:
    """Tests for install_optimizations (mocked)."""

    def test_skips_without_gpu(self) -> None:
        """Should skip entirely if no NVIDIA GPU is found."""
        from src.installer.optimizations import install_optimizations

        log = MagicMock()
        with patch("src.installer.optimizations.detect_nvidia_gpu", return_value=False):
            install_optimizations(MagicMock(), MagicMock(), MagicMock(), MagicMock(), log)

        log.info.assert_called_once()
        assert "No NVIDIA GPU" in log.info.call_args[0][0]
