from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer, Static, Markdown
from api.client import ZeroOpsClient
from utils.config import settings
import webbrowser

from .modals import QuitScreen, SubmissionResultScreen
from .leaderboard import Leaderboard


class Dashboard(Screen):
    """Main dashboard showing user progress."""

    CSS = """
    Dashboard {
        layout: vertical;
        width: 100%;
        height: 100%;
    }
    
    #top-bar {
        height: auto;
        width: 100%;
        padding: 1 2;
        layout: vertical;
        margin-bottom: 1;
    }

    #user-label, #status-label {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
    }
    
    #exercise-label {
        text-style: bold;
        color: $success;
        margin-bottom: 0;
    }

    #rendu-label {
        text-style: bold;
        color: $error;
        margin-bottom: 0;
    }
    
    #subject {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        margin: 1 0;
        padding: 1 2;
        min-height: 10;
    }

    #actions {
        height: 5;
        align: center middle;
        layout: horizontal;
        padding-bottom: 1;
        width: 100%;
    }

    #actions Button {
        margin: 0 2;
        min-width: 16;
    }

    Markdown {
        padding: 1;
    }
    
    """

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Handle link clicks in markdown."""
        if event.href:
            self.notify(f"Opening {event.href}...", severity="information")
            webbrowser.open(event.href)

    def compose(self) -> ComposeResult:
        yield Header()

        yield Container(
            Label(f"User: {settings.USER_ID}", id="user-label"),
            Static("Level: ...", id="status-label", classes="stat"),
            Static("Exercise: ...", id="exercise-label", classes="stat"),
            Static("Rendu: ...", id="rendu-label", classes="stat"),
            id="top-bar",
        )

        yield ScrollableContainer(
            Markdown("Loading subject...", id="subject-md"), id="subject"
        )

        yield Container(
            Button("Submit", variant="primary", id="submit"),
            Button("Leaderboard", variant="primary", id="leaderboard"),
            Button("Quit", variant="primary", id="quit"),
            id="actions",
        )

        yield Footer()

    async def on_mount(self) -> None:
        """Load status when screen mounts."""
        await self.refresh_status()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.push_screen(QuitScreen())
        elif event.button.id == "submit":
            await self.submit_exercise()
        elif event.button.id == "leaderboard":
            self.app.push_screen(Leaderboard())

    async def refresh_status(self):
        client = ZeroOpsClient()
        try:
            data = await client.get_status()
        except Exception as e:
            self.notify(f"Connection error: {e}", severity="error")
            data = {"status": "error", "message": "Failed to connect to server."}
        finally:
            await client.close()

        if data.get("status") == "ok":
            self.query_one("#subject").styles.display = "block"
            self.query_one("#submit").disabled = False

            self.query_one("#status-label", Static).update(
                f"Level: {data.get('current_level')}"
            )
            ex_id = data.get("current_exercise")
            self.query_one("#exercise-label", Static).update(
                f"Exercise: {ex_id or 'None'}"
            )
            self.query_one("#rendu-label", Static).update(
                f"Rendu: ~/rendudevops/{ex_id or '...'}"
            )
            self.current_exercise = ex_id

            if ex_id:
                client = ZeroOpsClient()
                try:
                    details = await client.get_exercise_details(ex_id)
                except Exception as e:
                    self.notify(
                        f"Failed to load exercise details: {e}", severity="error"
                    )
                    details = {}
                finally:
                    await client.close()

                self.query_one("#subject-md", Markdown).update(
                    details.get("subject", "No subject.")
                )

                self._ensure_workspace_ready(ex_id)
            else:
                self.query_one("#subject-md", Markdown).update("No active exercise.")
        else:
            self.query_one("#status-label", Static).update(
                f"Error: {data.get('message', 'Unknown')}"
            )

    def _ensure_workspace_ready(self, ex_id: str) -> None:
        """Ensure local workspace directories exist."""
        if not settings.RENDU_DIR.exists():
            try:
                settings.RENDU_DIR.mkdir(parents=True, exist_ok=True)
                self.notify(
                    f"Created workspace at {settings.RENDU_DIR}", severity="information"
                )
            except Exception as e:
                self.notify(f"Could not create workspace: {e}", severity="error")

        ex_dir = settings.RENDU_DIR / ex_id
        if not ex_dir.exists():
            try:
                ex_dir.mkdir(exist_ok=True)
                self.notify(f"Created directory for {ex_id}", severity="information")
            except Exception as e:
                self.notify(f"Could not create exercise dir: {e}", severity="error")

    def _collect_exercise_code(
        self, exercise_dir, target_files, exercise_type
    ) -> tuple[str, list]:
        """Read and concatenate all relevant exercise files."""
        code_parts = []
        files_found = []

        def read_file(path):
            try:
                with open(path, "r") as f:
                    return f.read()
            except Exception as e:
                self.notify(f"Error reading {path.name}: {e}", severity="error")
                return None

        for target in target_files:
            file_path = exercise_dir / target
            if file_path.exists():
                files_found.append(target)
                content = read_file(file_path)
                if content is not None:
                    code_parts.append(content)

        if exercise_type == "kubernetes":
            for ext in ["*.yaml", "*.yml"]:
                for fpath in exercise_dir.glob(ext):
                    if fpath.name not in files_found:
                        files_found.append(fpath.name)
                        content = read_file(fpath)
                        if content is not None:
                            code_parts.append(content)

        return "\n---\n".join(code_parts), files_found

    async def submit_exercise(self):
        if not hasattr(self, "current_exercise") or not self.current_exercise:
            self.notify("No active exercise to submit!", severity="warning")
            return

        self.notify(f"Submitting {self.current_exercise}...", severity="information")

        client = ZeroOpsClient()
        details = {}
        try:
            details = await client.get_exercise_details(self.current_exercise)
        except Exception as e:
            self.notify(f"Failed to get exercise details: {e}", severity="error")
            return
        finally:
            await client.close()

        exercise_type = details.get("type", "python")

        target_files = self._get_target_files(exercise_type)

        exercise_dir = settings.RENDU_DIR / self.current_exercise

        code_to_submit, files_found = self._collect_exercise_code(
            exercise_dir, target_files, exercise_type
        )

        if target_files and not files_found:
            expected = ", ".join(target_files)
            self.notify(f"No files found. Expected: {expected}", severity="error")
            return

        client = ZeroOpsClient()
        try:
            data = await client.submit_exercise(
                self.current_exercise, code=code_to_submit
            )
        except Exception as e:
            self.notify(f"Submission failed: {e}", severity="error")
            return
        finally:
            await client.close()

        is_success = data.get("status") == "success"
        message = data.get("message", "Unknown result")

        self.app.push_screen(
            SubmissionResultScreen(
                success=is_success, message=message, exercise_id=self.current_exercise
            )
        )

        if is_success:
            await self.refresh_status()

    def _get_target_files(self, exercise_type: str) -> list:
        """Return list of expected files based on exercise type."""
        file_mapping = {
            "python": ["main.py"],
            "docker": ["Dockerfile"],
            "kubernetes": [
                "deployment.yaml",
                "service.yaml",
                "pod.yaml",
                "configmap.yaml",
                "secret.yaml",
                "ingress.yaml",
                "pv.yaml",
                "pvc.yaml",
                "namespace.yaml",
                "replicaset.yaml",
            ],
            "docker-compose": ["docker-compose.yaml", "docker-compose.yml"],
            "prometheus": ["prometheus.yml", "prometheus.yaml", "alerting-rules.yml"],
            "grafana": ["dashboard.json", "datasource.yaml"],
            "terraform": ["main.tf", "variables.tf", "outputs.tf"],
            "ansible": ["playbook.yaml", "playbook.yml", "inventory.ini"],
            "helm": ["Chart.yaml", "values.yaml"],
            "shell": ["script.sh", "main.sh"],
            "c": ["main.c", "Makefile"],
            "interactive": [],
        }
        return file_mapping.get(exercise_type, ["main.py"])
