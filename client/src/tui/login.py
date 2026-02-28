from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer, Input
from utils.config import settings

from .dashboard import Dashboard


class LoginScreen(Screen):
    """Screen for simple user id entry."""

    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-container {
        width: 60;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }

    .instruction {
        margin-bottom: 2;
        text-align: center;
    }

    #user-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #login-btn {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Welcome to ZeroOps", classes="title"),
            Label("Enter your User ID to continue.", classes="instruction"),
            Input(placeholder="User ID (e.g., student1)", id="user-input"),
            Button("Login", variant="primary", id="login-btn"),
            id="login-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self.do_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.do_login()

    def do_login(self) -> None:
        user_input = self.query_one("#user-input", Input)
        user_id = user_input.value.strip()

        if user_id:
            settings.USER_ID = user_id
            self.notify(f"Welcome, {user_id}!", severity="success")
            self.app.switch_screen(Dashboard())
        else:
            self.notify("Please enter a User ID.", severity="error")
