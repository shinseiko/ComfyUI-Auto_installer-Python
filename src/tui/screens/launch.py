"""
Launch Screen — Configure and start ComfyUI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.settings import UserSettings


class LaunchScreen(Screen):
    """Configure and launch ComfyUI."""

    BINDINGS = [("escape", "app.back", "Back")]

    def __init__(
        self,
        install_path: Path,
        settings: UserSettings,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.install_path = install_path
        self.user_settings = settings

    def compose(self) -> ComposeResult:
        """Build the launch screen layout."""
        s = self.user_settings

        config_text = (
            f"[b]Listen:[/b]  {s.listen_address}\n"
            f"[b]VRAM:[/b]    {s.vram_mode}\n"
            f"[b]Sage:[/b]    {'✅' if s.use_sage_attention else '❌'}\n"
            f"[b]Browser:[/b] {'✅' if s.auto_launch_browser else '❌'}"
        )

        args = s.build_comfyui_args()
        args_preview = " ".join(args)

        with Vertical(id="launch-container"):
            yield Static(
                "[b]🚀 Launch ComfyUI[/b]\n\n" + config_text,
                id="launch-panel",
            )
            yield Static(
                f"[dim]Args: python main.py --windows-standalone-build {args_preview}[/dim]",
            )
            yield Button(
                "🚀  Launch ComfyUI",
                id="launch-button",
                variant="success",
            )
            with Center():
                yield Button("← Back", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "launch-button":
            self._launch_comfyui()

    def _launch_comfyui(self) -> None:
        """Launch ComfyUI and exit TUI."""
        comfy_path = self.install_path / "ComfyUI"
        python_exe = self.install_path / "python_embeded" / "python.exe"

        if not python_exe.exists():
            # Non-portable: use system python
            python_exe = Path(sys.executable)

        if not (comfy_path / "main.py").exists():
            self.app.bell()
            return

        args = [str(python_exe), "-s", str(comfy_path / "main.py")]

        # Add standalone flag for portable builds
        if (self.install_path / "python_embeded").exists():
            args.append("--windows-standalone-build")

        args.extend(self.user_settings.build_comfyui_args())

        # Exit TUI and launch
        self.app.exit()
        subprocess.Popen(  # noqa: S603
            args,
            cwd=str(self.install_path),
        )
