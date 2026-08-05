"""
Onboarding screen — shown after first GitHub login when no repository is linked.

Presents Option 2: link an existing GitHub repository.
The student provides owner/repo and the server verifies ownership.

Designed so that Option 1 (create from template) can be added later
by mounting an additional tab or step without changing this file's structure.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer, Input, Static
from api.client import ZeroOpsClient
from utils.config import settings


class OnboardingScreen(Screen):
    """Repository linking wizard shown after first GitHub login."""

    CSS = """
    OnboardingScreen {
        align: center middle;
    }

    #onboarding-container {
        width: 70;
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

    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .hint {
        color: $text-muted;
        margin-bottom: 1;
    }

    .input-label {
        margin-bottom: 0;
        color: $text;
    }

    #owner-input, #repo-input {
        width: 100%;
        margin-bottom: 1;
    }

    #link-btn {
        width: 100%;
        margin-top: 1;
    }

    #status-label {
        text-align: center;
        margin-top: 1;
        min-height: 1;
    }

    #format-hint {
        color: $text-muted;
        margin-bottom: 2;
        text-align: center;
    }

    .divider {
        width: 100%;
        height: 1;
        border-bottom: solid $primary;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("🔗  Link Your Repository", classes="title"),
            Label(
                f"Welcome, @{settings.USER_ID}! Let's connect your GitHub repository.",
                classes="subtitle",
            ),

            Static("", classes="divider"),

            Label("Link an Existing Repository", classes="section-title"),
            Label(
                "Enter the GitHub repository you will use for ZeroOps exercises.",
                classes="hint",
            ),
            Label("The repository must be owned by your GitHub account.", classes="hint"),

            Static("", classes="divider"),

            Label("Repository Owner (your GitHub username):", classes="input-label"),
            Input(
                placeholder=f"e.g. {settings.USER_ID}",
                id="owner-input",
            ),
            Label("Repository Name:", classes="input-label"),
            Input(
                placeholder="e.g. zeroops-devops",
                id="repo-input",
            ),
            Label("Format:  owner/repo", id="format-hint"),

            Button("Link Repository", variant="primary", id="link-btn"),
            Label("", id="status-label"),

            id="onboarding-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        # Pre-fill owner with the logged-in GitHub username
        try:
            self.query_one("#owner-input", Input).value = settings.USER_ID
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "link-btn":
            await self._link_repository()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        await self._link_repository()

    async def _link_repository(self) -> None:
        owner = self.query_one("#owner-input", Input).value.strip()
        repo = self.query_one("#repo-input", Input).value.strip()

        if not owner or not repo:
            self._set_status("Please fill in both owner and repository name.", error=True)
            return

        self._set_status(f"Verifying '{owner}/{repo}'... (checking ownership)")
        self.query_one("#link-btn", Button).disabled = True

        client = ZeroOpsClient()
        try:
            result = await client.link_repo(owner, repo)
        except Exception as e:
            result = {"status": "error", "message": str(e)}
        finally:
            await client.close()

        self.query_one("#link-btn", Button).disabled = False

        if result.get("status") == "linked":
            repo_info = result.get("repository", {})
            full_name = repo_info.get("full_name", f"{owner}/{repo}")
            self.notify(
                f"Repository '{full_name}' linked! 🚀",
                severity="success",
                timeout=4,
            )
            from tui.dashboard import Dashboard
            self.app.switch_screen(Dashboard())
        else:
            message = result.get("message", "Failed to link repository.")
            self._set_status(f"⚠ {message}", error=True)

    def _set_status(self, message: str, error: bool = False) -> None:
        label = self.query_one("#status-label", Label)
        label.update(message)
        if error:
            label.add_class("error-label")
        else:
            label.remove_class("error-label")
