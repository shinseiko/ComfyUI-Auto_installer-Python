"""Tests for the model download engine — v3 hierarchical catalog."""

import json
from pathlib import Path

import pytest

from src.downloader.engine import (
    load_catalog,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def v3_catalog(tmp_path: Path) -> Path:
    """Create a minimal v3 hierarchical catalog."""
    data = {
        "_manifest_version": 3,
        "_sources": {
            "huggingface": "https://hf.example.com/repo",
            "modelscope": "https://ms.example.com/repo",
        },
        "FLUX": {
            "_family_meta": {
                "display_name": "FLUX",
                "description": "Image generation",
            },
            "Dev": {
                "_meta": {"bundle_type": "image", "loader_type": "flux", "clip_type": "t5"},
                "fp16": {
                    "min_vram": 30,
                    "files": [
                        {
                            "path": "diffusion_models/FLUX/flux-dev-fp16.safetensors",
                            "path_type": "flux_diff",
                            "sha256": "abc123",
                            "size_mb": 22000,
                        },
                    ],
                },
                "GGUF_Q4": {
                    "min_vram": 12,
                    "files": [
                        {
                            "path": "diffusion_models/FLUX/Flux1-Dev-Q4_K_S.gguf",
                            "path_type": "flux_diff",
                            "sha256": "def456",
                            "size_mb": 6500,
                        },
                    ],
                },
            },
            "Fill": {
                "_meta": {"bundle_type": "image_inpaint"},
                "GGUF_Q4": {
                    "min_vram": 12,
                    "files": [
                        {
                            "path": "diffusion_models/FLUX/Flux1-Fill-Q4_K_S.gguf",
                            "path_type": "flux_diff",
                            "sha256": "ghi789",
                            "size_mb": 6500,
                        },
                    ],
                },
            },
        },
        "WAN_2.1": {
            "_family_meta": {
                "display_name": "WAN 2.1",
                "description": "Video generation",
            },
            "T2V": {
                "_meta": {"bundle_type": "video", "loader_type": "wan"},
                "GGUF_Q8": {
                    "min_vram": 24,
                    "files": [
                        {
                            "path": "diffusion_models/WAN/Wan2.1-T2V-14B-Q8_0.gguf",
                            "path_type": "wan_diff",
                            "sha256": "jkl012",
                            "size_mb": 14000,
                        },
                    ],
                },
            },
        },
    }
    path = tmp_path / "model_manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test: catalog does not mutate input
# ---------------------------------------------------------------------------

class TestCatalogNoMutation:
    """Ensure load_catalog does not mutate the raw JSON data."""

    def test_load_does_not_mutate_input(self, v3_catalog: Path):
        """Loading the catalog twice should produce identical results."""
        cat1 = load_catalog(v3_catalog)
        cat2 = load_catalog(v3_catalog)
        # If load_catalog mutated the file data, the second load would differ
        assert len(cat1.bundles) == len(cat2.bundles)
        assert len(cat1.families) == len(cat2.families)
        for key in cat1.bundles:
            assert key in cat2.bundles


# ---------------------------------------------------------------------------
# Test: v3 hierarchical catalog
# ---------------------------------------------------------------------------

class TestLoadCatalogV3:
    """Verify v3 hierarchical catalogs load correctly."""

    def test_loads_v3(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert cat.manifest_version == 3

    def test_v3_compound_keys(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert "FLUX/Dev" in cat.bundles
        assert "FLUX/Fill" in cat.bundles
        assert "WAN_2.1/T2V" in cat.bundles

    def test_v3_family_count(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert len(cat.families) == 2

    def test_v3_family_meta(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert cat.families["FLUX"].display_name == "FLUX"
        assert cat.families["FLUX"].description == "Image generation"
        assert cat.families["WAN_2.1"].display_name == "WAN 2.1"

    def test_v3_bundle_family_field(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert cat.bundles["FLUX/Dev"].family == "FLUX"
        assert cat.bundles["WAN_2.1/T2V"].family == "WAN_2.1"

    def test_v3_bundle_meta(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert cat.bundles["FLUX/Dev"].meta.bundle_type == "image"
        assert cat.bundles["FLUX/Dev"].meta.loader_type == "flux"
        assert cat.bundles["FLUX/Fill"].meta.bundle_type == "image_inpaint"

    def test_v3_variants(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        dev = cat.bundles["FLUX/Dev"]
        assert "fp16" in dev.variants
        assert "GGUF_Q4" in dev.variants
        assert dev.variants["fp16"].min_vram == 30
        assert dev.variants["GGUF_Q4"].min_vram == 12

    def test_v3_files(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        files = cat.bundles["FLUX/Dev"].variants["fp16"].files
        assert len(files) == 1
        assert files[0].path == "diffusion_models/FLUX/flux-dev-fp16.safetensors"
        assert files[0].sha256 == "abc123"

    def test_v3_sources(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert cat.sources.huggingface == "https://hf.example.com/repo"

    def test_v3_total_bundles(self, v3_catalog: Path):
        cat = load_catalog(v3_catalog)
        assert len(cat.bundles) == 3  # FLUX/Dev, FLUX/Fill, WAN_2.1/T2V


# ---------------------------------------------------------------------------
# Test: edge cases
# ---------------------------------------------------------------------------

class TestCatalogEdgeCases:
    """Edge cases for catalog loading."""

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_catalog(tmp_path / "nonexistent.json")

    def test_empty_v3_family(self, tmp_path: Path):
        """A family with only _family_meta and no models."""
        data = {
            "_manifest_version": 3,
            "EMPTY": {
                "_family_meta": {"display_name": "Empty Family"},
            },
        }
        path = tmp_path / "model_manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        cat = load_catalog(path)
        assert len(cat.families) == 1
        assert len(cat.bundles) == 0

    def test_v3_missing_family_meta(self, tmp_path: Path):
        """Family without _family_meta still loads."""
        data = {
            "_manifest_version": 3,
            "TEST": {
                "ModelA": {
                    "_meta": {"bundle_type": "image"},
                    "fp16": {
                        "min_vram": 24,
                        "files": [],
                    },
                },
            },
        }
        path = tmp_path / "model_manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        cat = load_catalog(path)
        assert "TEST/ModelA" in cat.bundles
        assert cat.families["TEST"].display_name == ""


# ---------------------------------------------------------------------------
# Test: real manifest (optional, runs only if available)
# ---------------------------------------------------------------------------

class TestLoadRealModelManifest:
    """Test against the real model_manifest.json from the Assets repo."""

    _real_path = Path(r"Y:\ComfyUI-Auto_installer-Assets\model_manifest.json")

    def test_real_manifest_loads(self):
        if not self._real_path.exists():
            pytest.skip("Real model manifest not available")
        cat = load_catalog(self._real_path)
        assert cat.manifest_version >= 3

    def test_real_manifest_has_families(self):
        if not self._real_path.exists():
            pytest.skip("Real model manifest not available")
        cat = load_catalog(self._real_path)
        assert len(cat.families) >= 8  # FLUX, WAN_2.1, WAN_2.2, etc.

    def test_real_manifest_has_models(self):
        if not self._real_path.exists():
            pytest.skip("Real model manifest not available")
        cat = load_catalog(self._real_path)
        assert len(cat.bundles) >= 20

    def test_real_manifest_all_have_files(self):
        if not self._real_path.exists():
            pytest.skip("Real model manifest not available")
        cat = load_catalog(self._real_path)
        for name, bundle in cat.bundles.items():
            for vname, variant in bundle.variants.items():
                assert len(variant.files) > 0, f"{name}/{vname} has no files"

    def test_real_manifest_all_files_have_sha256(self):
        if not self._real_path.exists():
            pytest.skip("Real model manifest not available")
        cat = load_catalog(self._real_path)
        for name, bundle in cat.bundles.items():
            for vname, variant in bundle.variants.items():
                for f in variant.files:
                    assert f.sha256, f"{name}/{vname}: {f.path} missing sha256"
