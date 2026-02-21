from textual.app import ComposeResult
from textual.containers import Grid, Container, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

class SubmissionResultScreen(ModalScreen):
    """Modal screen to display submission results with details."""

    CSS = """
    SubmissionResultScreen {
        align: center middle;
    }

    #result-dialog {
        padding: 1 2;
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $background 80%;
        background: $surface;
    }

    #result-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    #result-title.success {
        color: $success;
    }

    #result-title.failure {
        color: $error;
    }

    #result-message {
        margin: 1 0;
        padding: 1;
        border: solid $primary;
        height: auto;
        max-height: 20;
        overflow-y: auto;
    }

    #result-close {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self, success: bool, message: str, exercise_id: str = ""):
        super().__init__()
        self.success = success
        self.message = message
        self.exercise_id = exercise_id

    def compose(self) -> ComposeResult:
        title_class = "success" if self.success else "failure"
        title_text = "✅ Submission Successful!" if self.success else "❌ Submission Failed"
        
        yield Container(
            Label(title_text, id="result-title", classes=title_class),
            Label(f"Exercise: {self.exercise_id}", id="result-exercise"),
            ScrollableContainer(
                Static(self.message, id="result-message-text"),
                id="result-message"
            ),
            Button("Close", variant="primary" if self.success else "error", id="result-close"),
            id="result-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "result-close":
            self.app.pop_screen()


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    CSS = """
    QuitScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()
