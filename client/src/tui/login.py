"""
GitHub OAuth login screen.

Flow:
  1. On mount: check for a saved JWT token.
     - Valid token → skip to Dashboard (or Onboarding if no repo linked).
     - No token → show "Login with GitHub" button.
  2. User clicks Login → server returns GitHub OAuth URL + state token.
  3. Client opens the URL in the system browser.
  4. Client polls /v1/auth/poll/{state} every 2 seconds.
  5. On completion: save JWT, check has_repository, route accordingly.
"""

import webbrowser
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer, LoadingIndicator
from utils.config import settings, load_token, save_token
from api.client import ZeroOpsClient


class LoginScreen(Screen):
    """GitHub OAuth login screen."""

    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-container {
        width: 64;
        height: auto;
        border: solid $accent;
        padding: 2 3;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    #github-btn {
        width: 100%;
        margin-bottom: 1;
    }

    #status-label {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #loading-indicator {
        width: 100%;
        height: 1;
        margin-top: 1;
        display: none;
    }

    #cancel-btn {
        width: 100%;
        display: none;
    }

    .error-label {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._poll_state: str | None = None
        self._poll_timer = None
        self._client: ZeroOpsClient | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("⚡ ZeroOps Workshop", classes="title"),
            Label("Sign in with your GitHub account to continue.", classes="subtitle"),
            Button("  Login with GitHub", variant="primary", id="github-btn"),
            Label("", id="status-label"),
            LoadingIndicator(id="loading-indicator"),
            Button("Cancel", variant="default", id="cancel-btn"),
            id="login-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Check for a stored token on startup."""
        await self._try_auto_login()

    async def _try_auto_login(self) -> None:
        token = load_token()
        if not token:
            return

        self.query_one("#status-label", Label).update("Verifying saved session...")
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
                from tui.dashboard import Dashboard
                self.app.switch_screen(Dashboard())
            else:
                from tui.onboarding import OnboardingScreen
                self.app.switch_screen(OnboardingScreen())
        else:
            # Saved token is invalid or expired — clear it and show login
            from utils.config import clear_token
            clear_token()
            self.query_one("#status-label", Label).update("")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "github-btn":
            await self._start_oauth()
        elif event.button.id == "cancel-btn":
            self._cancel_poll()

    async def _start_oauth(self) -> None:
        """Initiate OAuth: get URL from server, open browser, start polling."""
        self.query_one("#github-btn", Button).disabled = True
        self.query_one("#status-label", Label).update("Connecting to server...")

        self._client = ZeroOpsClient()
        try:
            data = await self._client.initiate_login()
        except Exception as e:
            self._show_error(f"Could not reach server: {e}")
            return

        if "error" in data or "auth_url" not in data:
            self._show_error("Failed to initiate login. Is the server running?")
            return

        auth_url = data["auth_url"]
        self._poll_state = data["state"]

        # Open browser
        webbrowser.open(auth_url)

        # Show waiting UI
        self.query_one("#status-label", Label).update(
            "Browser opened. Waiting for GitHub authorization..."
        )
        self.query_one("#loading-indicator", LoadingIndicator).styles.display = "block"
        self.query_one("#cancel-btn", Button).styles.display = "block"

        # Start polling every 2 seconds
        self._poll_timer = self.set_interval(2.0, self._poll_auth)

    async def _poll_auth(self) -> None:
        """Called every 2s by the interval timer to check OAuth completion."""
        if not self._poll_state or not self._client:
            return

        try:
            result = await self._client.poll_login(self._poll_state)
        except Exception:
            return

        status = result.get("status")

        if status == "complete":
            self._cancel_poll()
            token = result.get("token")
            if token:
                save_token(token)
                await self._on_login_success()
            else:
                self._show_error("Authentication completed but no token received.")

        elif status == "expired":
            self._cancel_poll()
            self._show_error("Authorization window expired. Please try again.")

    async def _on_login_success(self) -> None:
        """Fetch profile and route to the correct screen."""
        try:
            me = await self._client.get_me()
        except Exception:
            me = {}
        finally:
            await self._client.aclose()
            self._client = None

        settings.USER_ID = me.get("github_username", settings.USER_ID)
        self.notify(
            f"Welcome, @{settings.USER_ID}! 🎉", severity="success", timeout=4
        )

        if me.get("has_repository"):
            from tui.dashboard import Dashboard
            self.app.switch_screen(Dashboard())
        else:
            from tui.onboarding import OnboardingScreen
            self.app.switch_screen(OnboardingScreen())

    def _cancel_poll(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None
        self._poll_state = None

        # Reset UI
        try:
            self.query_one("#loading-indicator", LoadingIndicator).styles.display = "none"
            self.query_one("#cancel-btn", Button).styles.display = "none"
            self.query_one("#github-btn", Button).disabled = False
            self.query_one("#status-label", Label).update("")
        except Exception:
            pass

    def _show_error(self, message: str) -> None:
        self._cancel_poll()
        try:
            self.query_one("#status-label", Label).update(f"⚠ {message}")
            self.query_one("#status-label", Label).add_class("error-label")
        except Exception:
            self.notify(message, severity="error")
