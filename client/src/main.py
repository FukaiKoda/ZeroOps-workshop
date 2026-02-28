import typer
from textual.app import App
from utils.signals import setup_signal_handlers
from utils.config import settings
from tui.screens import QuitScreen, LoginScreen
import shutil

app = typer.Typer()


class ZeroOpsApp(App):
    """A Textual app for ZeroOps."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("ctrl+c", "request_quit", "Quit"),
    ]

    def on_mount(self) -> None:
        setup_signal_handlers(self.notify)
        self.push_screen(LoginScreen())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_request_quit(self) -> None:
        """Action to request quit with confirmation."""
        self.push_screen(QuitScreen())


@app.command()
def tui():
    """Start the TUI."""
    if settings.RENDU_DIR.exists():
        try:
            shutil.rmtree(settings.RENDU_DIR)
        except Exception as e:
            print(f"Warning: Failed to clean up {settings.RENDU_DIR}: {e}")

    settings.RENDU_DIR.mkdir(parents=True, exist_ok=True)

    tui_app = ZeroOpsApp()
    tui_app.run()


@app.command()
def version():
    """Show version."""
    print("ZeroOps Client")


if __name__ == "__main__":
    app()
