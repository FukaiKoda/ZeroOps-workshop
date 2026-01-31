from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Label, Header, Footer, Static, Markdown
from api.client import ZeroOpsClient
from utils.config import settings


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
        yield Container(
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


class Dashboard(Screen):
    """Main dashboard showing user progress."""

    CSS = """
    Dashboard {
        align: center middle;
    }

    #info-container {
        width: 80%;
        height: 80%;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .stat {
        margin: 1 0;
    }

    #subject {
        height: 1fr;
        border: solid $primary;
        margin: 1 0;
        padding: 1;
    }

    #actions {
        layout: horizontal;
        align: center middle;
        height: 3;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(f"Welcome, {settings.USER_ID}!", classes="title"),
            Static("Loading status...", id="status-label", classes="stat"),
            Static("Current Exercise: ...", id="exercise-label", classes="stat"),
            ScrollableContainer(
                Markdown("Loading subject...", id="subject-md"),
                id="subject",
            ),
            Container(
                Button("Refresh", variant="primary", id="refresh"),
                Button("Submit", variant="success", id="submit"),
                Button("Quit", variant="error", id="quit"),
                id="actions",
            ),
            id="info-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load status when screen mounts."""
        await self.refresh_status()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.push_screen(QuitScreen())
        elif event.button.id == "refresh":
            await self.refresh_status()
        elif event.button.id == "submit":
            await self.submit_exercise()

    async def refresh_status(self):
        client = ZeroOpsClient()
        profile = await client.get_me()
        if profile.get("error"):
            await client.close()
            self.query_one("#status-label", Static).update(
                f"Error: {profile.get('message', 'Unknown error')}"
            )
            return

        level = profile.get("current_level", 0)
        total_score = profile.get("total_score", 0)
        self.query_one("#status-label", Static).update(
            f"Level: {level} | Score: {total_score}"
        )

        exercise = await client.get_next_exercise()
        await client.close()

        if exercise.get("error"):
            self.query_one("#exercise-label", Static).update(
                f"Current Exercise: Error"
            )
            self.query_one("#subject-md", Markdown).update(
                exercise.get("message", "No subject available.")
            )
            return

        if "message" in exercise and not exercise.get("slug"):
            self.current_exercise_meta = None
            self.query_one("#exercise-label", Static).update(
                "Current Exercise: None"
            )
            self.query_one("#subject-md", Markdown).update(exercise.get("message"))
            return

        self.current_exercise_meta = exercise
        slug = exercise.get("slug")
        title = exercise.get("title") or slug
        self.query_one("#exercise-label", Static).update(
            f"Current Exercise: {title}"
        )

        client = ZeroOpsClient()
        details = await client.get_exercise_details(slug)
        await client.close()

        if details.get("error"):
            self.query_one("#subject-md", Markdown).update(
                details.get("message", "No subject available.")
            )
        else:
            subject = details.get("subject") or "No subject available."
            self.query_one("#subject-md", Markdown).update(subject)

        if not settings.RENDU_DIR.exists():
            try:
                settings.RENDU_DIR.mkdir(parents=True, exist_ok=True)
                self.notify(
                    f"Created workspace at {settings.RENDU_DIR}",
                    severity="information",
                )
            except Exception as e:
                self.notify(f"Could not create workspace: {e}", severity="error")

        ex_dir = settings.RENDU_DIR / slug
        if not ex_dir.exists():
            try:
                ex_dir.mkdir(exist_ok=True)
                self.notify(
                    f"Created directory for {slug}", severity="information"
                )
            except Exception as e:
                self.notify(f"Could not create exercise dir: {e}", severity="error")

    async def submit_exercise(self):
        if not getattr(self, "current_exercise_meta", None):
            self.notify("No active exercise to submit!", severity="warning")
            return

        slug = self.current_exercise_meta.get("slug")
        allowed_files = self.current_exercise_meta.get("allowed_files") or []
        stack = self.current_exercise_meta.get("stack")

        if allowed_files:
            target_file = allowed_files[0]
        elif stack == "docker":
            target_file = "Dockerfile"
        else:
            target_file = "main.py"

        file_path = settings.RENDU_DIR / slug / target_file
        if not file_path.exists():
            self.notify(
                f"Missing file: {target_file} in {slug}", severity="error"
            )
            return

        try:
            with open(file_path, "r") as f:
                code_to_submit = f.read()
        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")
            return

        client = ZeroOpsClient()
        response = await client.submit_exercise(
            slug,
            files=[{"filename": target_file, "content": code_to_submit}],
        )

        if response.get("error"):
            await client.close()
            self.notify(response.get("message", "Submission failed"), severity="error")
            return

        job_id = response.get("job_id")
        self.notify(
            f"Submission received. Job ID: {job_id}", severity="information"
        )

        if job_id:
            status = await client.get_job_status(job_id)
            await client.close()
            if status.get("error"):
                self.notify(status.get("message", "Status check failed"), severity="warning")
            else:
                job_status = status.get("status")
                if job_status in {"success", "failure"}:
                    result = status.get("result", {})
                    self.notify(
                        f"Result: {job_status.upper()} | Score: {result.get('score', 0)}",
                        severity="information" if job_status == "success" else "error",
                    )
                else:
                    self.notify(
                        f"Grading in progress: {job_status}", severity="information"
                    )
        else:
            await client.close()
