"""
Info Screen — Display system information.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


def _build_info_text() -> str:
    """Build formatted system info string."""
    lines = ["[b]ℹ️  System Information[/b]\n"]

    # Python
    lines.append(f"[b]Python:[/b]    {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    lines.append(f"[b]Platform:[/b]  {sys.platform}")

    # GPU
    try:
        from src.utils.gpu import get_gpu_vram_info, recommend_model_quality
        gpu = get_gpu_vram_info()
        if gpu:
            lines.append(f"\n[b]GPU:[/b]       {gpu.name}")
            lines.append(f"[b]VRAM:[/b]      {gpu.vram_gib} GB")
            lines.append(f"[b]Quality:[/b]   {recommend_model_quality(gpu.vram_gib)}")
        else:
            lines.append("\n[b]GPU:[/b]       [dim]Not detected[/dim]")
    except Exception:
        lines.append("\n[b]GPU:[/b]       [dim]Detection unavailable[/dim]")

    # PyTorch
    try:
        import torch
        lines.append(f"\n[b]PyTorch:[/b]   {torch.__version__}")
        if torch.cuda.is_available():
            lines.append(f"[b]CUDA:[/b]      {torch.version.cuda}")
    except ImportError:
        lines.append("\n[b]PyTorch:[/b]   [dim]Not installed[/dim]")

    # Tools
    try:
        from src.utils.commands import check_command_exists, get_command_version
        git_ver = get_command_version("git")
        lines.append(f"\n[b]Git:[/b]       {git_ver or '[dim]Not installed[/dim]'}")
        aria2 = check_command_exists("aria2c")
        lines.append(f"[b]aria2c:[/b]    {'[green]Available[/green]' if aria2 else '[dim]Not installed[/dim]'}")
        uv_ver = get_command_version("uv", "version")
        lines.append(f"[b]uv:[/b]        {uv_ver or '[dim]Not installed[/dim]'}")
    except Exception:
        pass

    return "\n".join(lines)


class InfoScreen(Screen):
    """System information display."""

    BINDINGS = [("escape", "app.back", "Back")]

    def compose(self) -> ComposeResult:
        """Build the info layout."""
        with Vertical(id="info-container"):
            yield Static(_build_info_text(), id="info-panel")
            with Center():
                yield Button("← Back", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back button."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
