"""
Download Screen — Model catalog browser and downloader.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class DownloadScreen(Screen):
    """Model download browser."""

    BINDINGS = [("escape", "app.back", "Back")]

    def __init__(self, install_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.install_path = install_path

    def compose(self) -> ComposeResult:
        """Build the download screen."""
        with Vertical(id="info-container"):
            yield Static(
                "[b]⬇️  Model Downloader[/b]\n\n"
                "This will launch the interactive model downloader.\n"
                "You'll be able to browse and select models by family,\n"
                "choose quality variants based on your GPU VRAM,\n"
                "and download with automatic mirror fallback.\n",
                id="info-panel",
            )
            with Center():
                yield Button(
                    "📥  Start Download Menu",
                    id="btn-start-download",
                    variant="primary",
                )
                yield Button("← Back", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-start-download":
            # Exit TUI and run download-models command
            self.app.exit(result="download-models")
