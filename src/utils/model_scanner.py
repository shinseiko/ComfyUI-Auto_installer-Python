"""Model security scanner for pickle-based model files.

Uses ``picklescan`` (the same library HuggingFace uses) to detect
potentially malicious code in ``.ckpt``, ``.pt``, and ``.pth`` model files.
Safetensors files are inherently safe and are skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Extensions that can contain arbitrary pickle code
UNSAFE_EXTENSIONS = {".ckpt", ".pt", ".pth", ".pkl", ".pickle"}

# Extensions known to be safe (no executable code)
SAFE_EXTENSIONS = {".safetensors", ".gguf", ".onnx"}


@dataclass
class ModelScanResult:
    """Result from scanning a single model file."""

    path: Path
    is_safe: bool
    issues_count: int = 0
    scan_error: bool = False
    error_message: str = ""


@dataclass
class DirectoryScanSummary:
    """Aggregated results from scanning a models directory."""

    total_scanned: int = 0
    safe_count: int = 0
    unsafe_count: int = 0
    error_count: int = 0
    skipped_safe_format: int = 0
    results: list[ModelScanResult] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return self.unsafe_count > 0


def scan_model_file(filepath: Path) -> ModelScanResult:
    """Scan a single model file for malicious pickle content.

    Args:
        filepath: Path to the model file to scan.

    Returns:
        ModelScanResult with safety status and issue details.
    """
    try:
        from picklescan.scanner import scan_file_path

        result = scan_file_path(str(filepath))
        return ModelScanResult(
            path=filepath,
            is_safe=result.infected_files == 0 and not result.scan_err,
            issues_count=result.issues_count,
            scan_error=result.scan_err,
        )
    except Exception as e:  # noqa: BLE001
        return ModelScanResult(
            path=filepath,
            is_safe=False,
            scan_error=True,
            error_message=str(e),
        )


def scan_models_directory(models_dir: Path) -> DirectoryScanSummary:
    """Recursively scan a models directory for unsafe pickle files.

    Scans all ``.ckpt``, ``.pt``, ``.pth``, ``.pkl`` files.
    Skips ``.safetensors``, ``.gguf``, ``.onnx`` (inherently safe).

    Args:
        models_dir: Root models directory to scan.

    Returns:
        DirectoryScanSummary with aggregated results.
    """
    summary = DirectoryScanSummary()

    if not models_dir.exists():
        return summary

    # Count safe-format files for the summary
    for safe_ext in SAFE_EXTENSIONS:
        summary.skipped_safe_format += len(
            list(models_dir.rglob(f"*{safe_ext}"))
        )

    # Find and scan all potentially unsafe files
    unsafe_files: list[Path] = []
    for ext in UNSAFE_EXTENSIONS:
        unsafe_files.extend(models_dir.rglob(f"*{ext}"))

    for filepath in sorted(unsafe_files):
        result = scan_model_file(filepath)
        summary.results.append(result)
        summary.total_scanned += 1

        if result.scan_error:
            summary.error_count += 1
        elif result.is_safe:
            summary.safe_count += 1
        else:
            summary.unsafe_count += 1

    return summary
