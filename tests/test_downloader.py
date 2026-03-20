"""Tests for the unified model downloader engine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from src.downloader.engine import (
    DEFAULT_PATH_MAPPING,
    ModelFile,
    SourcesConfig,
    _build_download_urls,
    load_catalog,
    resolve_file_path,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_catalog_json(tmp_path: Path) -> Path:
    """Create a minimal v3 catalog JSON for testing."""
    data = {
        "_manifest_version": 3,
        "_sources": {
            "huggingface": "https://hf.example.com/repo",
            "modelscope": "https://ms.example.com/repo",
        },
        "TEST_MODEL": {
            "_family_meta": {
                "display_name": "Test Model",
                "description": "For testing",
            },
            "fp16": {
                "_meta": {
                    "loader_type": "test",
                    "clip_type": "test",
                },
                "fp16": {
                    "min_vram": 24,
                    "files": [
                        {
                            "path": "diffusion_models/FLUX/model-fp16.safetensors",
                            "path_type": "flux_diff",
                        },
                        {
                            "path": "clip/clip_l.safetensors",
                            "path_type": "clip",
                        },
                    ],
                },
                "GGUF_Q4": {
                    "min_vram": 8,
                    "files": [
                        {
                            "path": "unet/FLUX/model-Q4_K_S.gguf",
                            "path_type": "flux_unet",
                        },
                    ],
                },
            },
            "EMPTY": {
                "_meta": {"loader_type": "empty"},
            },
        },
    }
    path = tmp_path / "test_catalog.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return path


class TestLoadCatalog:
    """Tests for v3 catalog loading."""

    def test_load_valid(self, sample_catalog_json: Path) -> None:
        catalog = load_catalog(sample_catalog_json)
        assert "TEST_MODEL/fp16" in catalog.bundles
        assert "TEST_MODEL/EMPTY" in catalog.bundles

    def test_bundle_meta(self, sample_catalog_json: Path) -> None:
        catalog = load_catalog(sample_catalog_json)
        bundle = catalog.bundles["TEST_MODEL/fp16"]
        assert bundle.meta.loader_type == "test"

    def test_variants_parsed(self, sample_catalog_json: Path) -> None:
        catalog = load_catalog(sample_catalog_json)
        bundle = catalog.bundles["TEST_MODEL/fp16"]
        assert "fp16" in bundle.variants
        assert "GGUF_Q4" in bundle.variants
        assert bundle.variants["fp16"].min_vram == 24
        assert bundle.variants["GGUF_Q4"].min_vram == 8

    def test_files_parsed(self, sample_catalog_json: Path) -> None:
        catalog = load_catalog(sample_catalog_json)
        variant = catalog.bundles["TEST_MODEL/fp16"].variants["fp16"]
        assert len(variant.files) == 2
        assert variant.files[0].path_type == "flux_diff"
        assert variant.files[0].filename == "model-fp16.safetensors"
        assert variant.files[1].path_type == "clip"

    def test_empty_bundle(self, sample_catalog_json: Path) -> None:
        catalog = load_catalog(sample_catalog_json)
        bundle = catalog.bundles["TEST_MODEL/EMPTY"]
        assert len(bundle.variants) == 0

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_catalog(tmp_path / "nonexistent.json")


class TestResolveFilePath:
    """Tests for path_type → directory resolution."""

    def test_known_path_types(self, tmp_path: Path) -> None:
        """All registered path types resolve correctly."""
        for path_type, expected_subdir in DEFAULT_PATH_MAPPING.items():
            result = resolve_file_path(tmp_path, path_type, "test.bin", DEFAULT_PATH_MAPPING)
            assert result == tmp_path / expected_subdir / "test.bin"

    def test_unknown_path_type(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unknown path_type"):
            resolve_file_path(tmp_path, "nonexistent_type", "test.bin", DEFAULT_PATH_MAPPING)

    def test_flux_diff(self, tmp_path: Path) -> None:
        result = resolve_file_path(tmp_path, "flux_diff", "model.safetensors", DEFAULT_PATH_MAPPING)
        assert result == tmp_path / "diffusion_models" / "FLUX" / "model.safetensors"

    def test_clip(self, tmp_path: Path) -> None:
        result = resolve_file_path(tmp_path, "clip", "t5xxl.safetensors", DEFAULT_PATH_MAPPING)
        assert result == tmp_path / "clip" / "t5xxl.safetensors"

    def test_vae(self, tmp_path: Path) -> None:
        result = resolve_file_path(tmp_path, "vae", "ae.safetensors", DEFAULT_PATH_MAPPING)
        assert result == tmp_path / "vae" / "ae.safetensors"


class TestModelFileAndUrls:
    """Tests for ModelFile and URL construction."""

    def test_filename_from_path(self) -> None:
        """filename property derives name from path."""
        f = ModelFile(path="diffusion_models/FLUX/model-fp16.safetensors", path_type="flux_diff")
        assert f.filename == "model-fp16.safetensors"

    def test_build_download_urls(self) -> None:
        """URLs are built from both mirrors."""
        sources = SourcesConfig(
            huggingface="https://hf.example.com/repo",
            modelscope="https://ms.example.com/repo",
        )
        f = ModelFile(path="clip/test.bin", path_type="clip")
        urls = _build_download_urls(f, sources)
        assert len(urls) == 2
        assert urls[0] == "https://hf.example.com/repo/clip/test.bin"
        assert urls[1] == "https://ms.example.com/repo/clip/test.bin"

    def test_build_urls_empty_sources(self) -> None:
        """Empty sources produce no URLs."""
        f = ModelFile(path="clip/test.bin", path_type="clip")
        urls = _build_download_urls(f, SourcesConfig())
        assert urls == []
