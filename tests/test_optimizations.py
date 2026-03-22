"""Tests for the performance optimizations module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.config import InstallOptions, OptimizationPackage
from src.installer.optimizations import (
    _check_package_installed,
    _check_requirements,
    _get_cuda_version_from_torch,
    _get_torch_version,
    _resolve_torch_constraint,
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


class TestResolveTorchConstraint:
    """Tests for _resolve_torch_constraint."""

    def test_torch_2_10(self) -> None:
        assert _resolve_torch_constraint("2.10.0+cu130", {}) == ">=3.5,<4"

    def test_torch_2_8(self) -> None:
        assert _resolve_torch_constraint("2.8.0+cu128", {}) == ">=3.4,<3.5"

    def test_torch_2_7(self) -> None:
        assert _resolve_torch_constraint("2.7.0+cu124", {}) == ">=3.3,<3.4"

    def test_torch_2_6(self) -> None:
        assert _resolve_torch_constraint("2.6.0+cu121", {}) == ">=3.2,<3.3"

    def test_torch_old(self) -> None:
        assert _resolve_torch_constraint("2.5.0", {}) == "<3.2"

    def test_invalid_version(self) -> None:
        assert _resolve_torch_constraint("not-a-version", {}) == ""

    def test_config_driven_constraint(self) -> None:
        """Config-driven constraints override hardcoded table."""
        constraints = {"2.10": ">=4.0,<5"}
        assert _resolve_torch_constraint("2.10.0+cu130", constraints) == ">=4.0,<5"


class TestCheckRequirements:
    """Tests for _check_requirements."""

    def test_nvidia_only_with_nvidia(self) -> None:
        assert _check_requirements(["nvidia"], has_nvidia=True, platform="windows")

    def test_nvidia_only_without_nvidia(self) -> None:
        assert not _check_requirements(["nvidia"], has_nvidia=False, platform="windows")

    def test_nvidia_and_linux_on_linux(self) -> None:
        assert _check_requirements(["nvidia", "linux"], has_nvidia=True, platform="linux")

    def test_nvidia_and_linux_on_windows(self) -> None:
        """flash-attn scenario: requires nvidia+linux, but we're on windows."""
        assert not _check_requirements(["nvidia", "linux"], has_nvidia=True, platform="windows")

    def test_no_requirements(self) -> None:
        """Empty requires = always install."""
        assert _check_requirements([], has_nvidia=False, platform="macos")

    def test_amd_requirement(self) -> None:
        assert _check_requirements(["amd"], has_nvidia=False, has_amd=True, platform="linux")


class TestOptimizationPackage:
    """Tests for OptimizationPackage.get_package_name."""

    def test_string_package(self) -> None:
        pkg = OptimizationPackage(name="test", pypi_package="testpkg")
        assert pkg.get_package_name("windows") == "testpkg"
        assert pkg.get_package_name("linux") == "testpkg"

    def test_dict_package_windows(self) -> None:
        pkg = OptimizationPackage(
            name="triton",
            pypi_package={"windows": "triton-windows", "linux": "triton"},
        )
        assert pkg.get_package_name("windows") == "triton-windows"
        assert pkg.get_package_name("linux") == "triton"
        assert pkg.get_package_name("macos") is None


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

    def test_filters_by_platform(self) -> None:
        """Linux-only packages should be filtered on Windows."""
        from src.installer.optimizations import install_optimizations

        log = MagicMock()
        deps = MagicMock()
        deps.optimizations.packages = [
            OptimizationPackage(
                name="flash-attn",
                pypi_package="flash-attn",
                requires=["nvidia", "linux"],
            ),
        ]

        with (
            patch("src.installer.optimizations.detect_nvidia_gpu", return_value=True),
            patch("src.installer.optimizations._get_current_platform", return_value="windows"),
            patch("src.installer.optimizations._get_cuda_version_from_torch", return_value="13.0"),
            patch("src.installer.optimizations._get_torch_version", return_value="2.10.0"),
            patch("src.installer.optimizations.install_sageattention"),
        ):
            install_optimizations(MagicMock(), MagicMock(), MagicMock(), deps, log)

        # flash-attn should have been skipped (requires linux)
        log.info.assert_any_call("flash-attn: skipped (requires ['nvidia', 'linux'], env=windows).")

    def test_installs_compatible_package(self) -> None:
        """Compatible packages should trigger uv_install."""
        from src.installer.optimizations import install_optimizations

        log = MagicMock()
        deps = MagicMock()
        deps.optimizations.packages = [
            OptimizationPackage(
                name="triton",
                pypi_package="triton",
                requires=["nvidia"],
                install_options=InstallOptions(no_build_isolation=False),
            ),
        ]

        with (
            patch("src.installer.optimizations.detect_nvidia_gpu", return_value=True),
            patch("src.installer.optimizations._get_current_platform", return_value="linux"),
            patch("src.installer.optimizations._get_cuda_version_from_torch", return_value="13.0"),
            patch("src.installer.optimizations._get_torch_version", return_value="2.10.0"),
            patch("src.installer.optimizations._check_package_installed", return_value=None),
            patch("src.installer.optimizations.uv_install") as mock_uv,
            patch("src.installer.optimizations.install_sageattention"),
        ):
            install_optimizations(MagicMock(), MagicMock(), MagicMock(), deps, log)

        mock_uv.assert_called_once()


class TestSageAttentionWheelConfig:
    """Tests for SageAttentionWheelConfig.matches_gpu."""

    def test_matches_ampere(self) -> None:
        from src.config import SageAttentionWheelConfig
        cfg = SageAttentionWheelConfig(
            name="sageattention",
            min_compute_capability=[8, 0],
            max_compute_capability=[9, 9],
        )
        assert cfg.matches_gpu((8, 0))
        assert cfg.matches_gpu((8, 6))
        assert cfg.matches_gpu((8, 9))
        assert cfg.matches_gpu((9, 0))

    def test_rejects_blackwell(self) -> None:
        from src.config import SageAttentionWheelConfig
        cfg = SageAttentionWheelConfig(
            name="sageattention",
            min_compute_capability=[8, 0],
            max_compute_capability=[9, 9],
        )
        assert not cfg.matches_gpu((10, 0))

    def test_blackwell_range(self) -> None:
        from src.config import SageAttentionWheelConfig
        cfg = SageAttentionWheelConfig(
            name="sageattention3",
            min_compute_capability=[10, 0],
            max_compute_capability=[99, 0],
        )
        assert cfg.matches_gpu((10, 0))
        assert not cfg.matches_gpu((9, 0))
        assert not cfg.matches_gpu((8, 9))


class TestGetComputeCapability:
    """Tests for get_compute_capability."""

    def test_gpu_detected(self) -> None:
        from src.utils.gpu import get_compute_capability
        mock_result = MagicMock(returncode=0, stdout="8.9\n")
        with patch("src.utils.gpu.subprocess.run", return_value=mock_result):
            assert get_compute_capability() == (8, 9)

    def test_blackwell(self) -> None:
        from src.utils.gpu import get_compute_capability
        mock_result = MagicMock(returncode=0, stdout="10.0\n")
        with patch("src.utils.gpu.subprocess.run", return_value=mock_result):
            assert get_compute_capability() == (10, 0)

    def test_no_gpu(self) -> None:
        from src.utils.gpu import get_compute_capability
        with patch("src.utils.gpu.subprocess.run", side_effect=FileNotFoundError):
            assert get_compute_capability() is None

    def test_bad_output(self) -> None:
        from src.utils.gpu import get_compute_capability
        mock_result = MagicMock(returncode=0, stdout="unknown\n")
        with patch("src.utils.gpu.subprocess.run", return_value=mock_result):
            assert get_compute_capability() is None

    def test_empty_output(self) -> None:
        from src.utils.gpu import get_compute_capability
        mock_result = MagicMock(returncode=0, stdout="\n")
        with patch("src.utils.gpu.subprocess.run", return_value=mock_result):
            assert get_compute_capability() is None


class TestInstallSageattention:
    """Tests for install_sageattention."""

    def test_already_installed(self) -> None:
        from src.installer.optimizations import install_sageattention
        log = MagicMock()
        deps = MagicMock()
        with patch("src.installer.optimizations._check_package_installed", return_value="2.1.0"):
            install_sageattention(MagicMock(), deps, log)
        log.sub.assert_any_call("SageAttention already installed: v2.1.0", style="success")

    def test_no_gpu_detected(self) -> None:
        from src.installer.optimizations import install_sageattention
        log = MagicMock()
        deps = MagicMock()
        with (
            patch("src.installer.optimizations._check_package_installed", return_value=None),
            patch("src.installer.optimizations.get_compute_capability", return_value=None),
        ):
            install_sageattention(MagicMock(), deps, log)
        log.info.assert_called_once()

    def test_wheel_match_and_install(self) -> None:
        from src.config import SageAttentionWheelConfig
        from src.installer.optimizations import install_sageattention

        log = MagicMock()
        deps = MagicMock()
        sa_wheel = SageAttentionWheelConfig(
            name="sageattention",
            min_compute_capability=[8, 0],
            max_compute_capability=[9, 9],
            versions={"cu130_cp311": "https://example.com/sa.whl"},
        )
        deps.pip_packages.sageattention_wheels = [sa_wheel]
        deps.mirrors = {}

        with (
            patch("src.installer.optimizations._check_package_installed", side_effect=[None, None, "2.1.0"]),
            patch("src.installer.optimizations.get_compute_capability", return_value=(8, 9)),
            patch("src.installer.optimizations._get_cuda_version_from_torch", return_value="13.0"),
            patch("src.installer.optimizations.sys") as mock_sys,
            patch("src.installer.optimizations.uv_install"),
            patch("src.utils.download.download_file"),
        ):
            mock_sys.version_info = MagicMock(major=3, minor=11)
            install_sageattention(MagicMock(), deps, log)

        log.sub.assert_any_call("Installing sageattention from pre-built wheel...")

    def test_no_wheel_falls_back_to_pypi(self) -> None:
        from src.installer.optimizations import install_sageattention

        log = MagicMock()
        deps = MagicMock()
        deps.pip_packages.sageattention_wheels = []
        deps.mirrors = {}

        with (
            patch("src.installer.optimizations._check_package_installed", side_effect=[None, None, "2.1.0"]),
            patch("src.installer.optimizations.get_compute_capability", return_value=(8, 9)),
            patch("src.installer.optimizations._get_cuda_version_from_torch", return_value="13.0"),
            patch("src.installer.optimizations.uv_install"),
        ):
            install_sageattention(MagicMock(), deps, log)

        log.sub.assert_any_call(
            "No pre-built SageAttention wheel available — trying PyPI (may need to compile)..."
        )

    def test_pypi_failure_warns(self) -> None:
        from src.installer.optimizations import install_sageattention

        log = MagicMock()
        deps = MagicMock()
        deps.pip_packages.sageattention_wheels = []
        deps.mirrors = {}

        with (
            patch("src.installer.optimizations._check_package_installed", return_value=None),
            patch("src.installer.optimizations.get_compute_capability", return_value=(8, 9)),
            patch("src.installer.optimizations._get_cuda_version_from_torch", return_value="13.0"),
            patch("src.installer.optimizations.uv_install"),
        ):
            install_sageattention(MagicMock(), deps, log)

        log.warning.assert_called()
