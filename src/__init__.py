"""ComfyUI Auto-Installer — Cross-platform automated installer for ComfyUI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("comfyui-auto-installer")
except PackageNotFoundError:
    __version__ = "5.0.0-dev"  # fallback for running from source without install

