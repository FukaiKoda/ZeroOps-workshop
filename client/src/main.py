import typer
from textual.app import App, ComposeResult
from utils.signals import setup_signal_handlers
from tui.screens import QuitScreen, Dashboard, LoginScreen

app = typer.Typer()

class ZeroOpsApp(App):
    """A Textual app for ZeroOps."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("ctrl+c", "request_quit", "Quit")
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
    tui_app = ZeroOpsApp()
    tui_app.run()

@app.command()
def version():
    """Show version."""
    print("ZeroOps Client v0.1.0")

if __name__ == "__main__":
    app()
