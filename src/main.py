# pyrefly: ignore [missing-import]
import typer
import shutil
# pyrefly: ignore [missing-import]
from textual.app import App
from utils.signals import setup_signal_handlers
from utils.config import settings, load_token, clear_token
from api.client import ZeroOpsClient
from tui.login import LoginScreen
from tui.dashboard import Dashboard
from tui.leaderboard import Leaderboard
from tui.onboarding import OnboardingScreen
from tui.modals import QuitScreen

app = typer.Typer()


class ZeroOpsApp(App):
    """A Textual app for ZeroOps."""

    SCREENS = {
        "login": LoginScreen,
        "onboarding": OnboardingScreen,
        "dashboard": Dashboard,
        "leaderboard": Leaderboard,
    }

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("ctrl+c", "request_quit", "Quit"),
    ]

    async def on_mount(self) -> None:
        setup_signal_handlers(self.notify)

        token = load_token()
        if token:
            client = ZeroOpsClient()
            try:
                me = await client.get_me()
            except Exception:
                me = {}
            finally:
                await client.close()

            if "github_username" in me:
                settings.USER_ID = me["github_username"]
                if me.get("has_repository"):
                    self.push_screen("dashboard")
                    return
                else:
                    self.push_screen("onboarding")
                    return
            else:
                clear_token()

        self.push_screen("login")

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
