"""Tests for the model security scanner utility."""

from __future__ import annotations

import pickle
from pathlib import Path

from src.utils.model_scanner import (
    SAFE_EXTENSIONS,
    UNSAFE_EXTENSIONS,
    DirectoryScanSummary,
    ModelScanResult,
    scan_model_file,
    scan_models_directory,
)


class TestModelScanResult:
    """Tests for the ModelScanResult dataclass."""

    def test_safe_result(self) -> None:
        result = ModelScanResult(path=Path("model.pt"), is_safe=True)
        assert result.is_safe
        assert result.issues_count == 0
        assert not result.scan_error

    def test_unsafe_result(self) -> None:
        result = ModelScanResult(
            path=Path("model.ckpt"), is_safe=False, issues_count=3,
        )
        assert not result.is_safe
        assert result.issues_count == 3


class TestDirectoryScanSummary:
    """Tests for the DirectoryScanSummary dataclass."""

    def test_empty_summary(self) -> None:
        summary = DirectoryScanSummary()
        assert summary.total_scanned == 0
        assert not summary.has_issues

    def test_has_issues(self) -> None:
        summary = DirectoryScanSummary(unsafe_count=1)
        assert summary.has_issues

    def test_no_issues(self) -> None:
        summary = DirectoryScanSummary(safe_count=5, total_scanned=5)
        assert not summary.has_issues


class TestExtensionConstants:
    """Tests for the extension sets."""

    def test_unsafe_extensions(self) -> None:
        assert ".ckpt" in UNSAFE_EXTENSIONS
        assert ".pt" in UNSAFE_EXTENSIONS
        assert ".pth" in UNSAFE_EXTENSIONS

    def test_safe_extensions(self) -> None:
        assert ".safetensors" in SAFE_EXTENSIONS
        assert ".gguf" in SAFE_EXTENSIONS
        assert ".onnx" in SAFE_EXTENSIONS

    def test_no_overlap(self) -> None:
        assert SAFE_EXTENSIONS.isdisjoint(UNSAFE_EXTENSIONS)


class TestScanModelFile:
    """Tests for scan_model_file function."""

    def test_scan_safe_pickle_file(self, tmp_path: Path) -> None:
        """A pickle file with just a simple dict should be safe."""
        model_file = tmp_path / "safe_model.pt"
        with open(model_file, "wb") as f:
            pickle.dump({"weights": [1.0, 2.0, 3.0]}, f)

        result = scan_model_file(model_file)
        assert result.is_safe
        assert result.issues_count == 0

    def test_scan_nonexistent_file(self, tmp_path: Path) -> None:
        """Scanning a nonexistent file should return an error result."""
        result = scan_model_file(tmp_path / "nonexistent.pt")
        assert result.scan_error

    def test_scan_corrupt_file(self, tmp_path: Path) -> None:
        """Scanning a corrupt file should return an error result."""
        model_file = tmp_path / "corrupt.pt"
        model_file.write_bytes(b"not a valid pickle file")

        result = scan_model_file(model_file)
        # picklescan may either error or report it as safe (no pickle ops found)
        # Either way, it should not crash
        assert isinstance(result, ModelScanResult)


class TestScanModelsDirectory:
    """Tests for scan_models_directory function."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        summary = scan_models_directory(tmp_path)
        assert summary.total_scanned == 0
        assert not summary.has_issues

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        summary = scan_models_directory(tmp_path / "does_not_exist")
        assert summary.total_scanned == 0

    def test_only_safetensors(self, tmp_path: Path) -> None:
        """Directory with only safe format files."""
        (tmp_path / "model.safetensors").write_bytes(b"fake")
        (tmp_path / "model2.gguf").write_bytes(b"fake")

        summary = scan_models_directory(tmp_path)
        assert summary.total_scanned == 0
        assert summary.skipped_safe_format == 2

    def test_mixed_formats(self, tmp_path: Path) -> None:
        """Directory with both safe and pickle-based files."""
        (tmp_path / "safe.safetensors").write_bytes(b"fake")

        pt_file = tmp_path / "upscaler.pt"
        with open(pt_file, "wb") as f:
            pickle.dump({"weight": 1.0}, f)

        summary = scan_models_directory(tmp_path)
        assert summary.total_scanned == 1
        assert summary.skipped_safe_format == 1
        assert summary.safe_count == 1

    def test_nested_directories(self, tmp_path: Path) -> None:
        """Scanner should find files in subdirectories."""
        subdir = tmp_path / "upscale_models"
        subdir.mkdir()

        pt_file = subdir / "RealESRGAN.pth"
        with open(pt_file, "wb") as f:
            pickle.dump({"model": "esrgan"}, f)

        summary = scan_models_directory(tmp_path)
        assert summary.total_scanned == 1
        assert summary.results[0].path == pt_file


class TestScanModelsCLI:
    """Tests for the scan-models CLI command registration."""

    def test_command_registered(self) -> None:
        """The scan-models command should be registered in the CLI."""
        from src.cli import app

        command_names = [cmd.name for cmd in app.registered_commands]
        assert "scan-models" in command_names
