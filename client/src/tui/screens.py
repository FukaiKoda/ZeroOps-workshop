from textual.app import ComposeResult
from textual.containers import Grid, Container, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Label, Header, Footer, Static, Markdown, DataTable, Input
from api.client import ZeroOpsClient
from utils.config import settings
import webbrowser
import uuid
from textual import work

class LoginScreen(Screen):
    """Screen for user authentication."""

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

    #login-btn {
        width: 100%;
        margin-bottom: 1;
    }
    
    #status-label {
        text-align: center;
        color: $warning;
        margin-top: 1;
        display: none;
    }
    """
    
    auth_state: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Welcome to ZeroOps", classes="title"),
            
            Label("Authenticate with 42 Intra to continue.", classes="instruction"),
            Button("Login with 42 Intra", variant="primary", id="login-btn"),
            
            Label("Waiting for authentication...", id="status-label"),
            
            id="login-container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            # Generate unique state
            self.auth_state = str(uuid.uuid4())
            
            # Open browser for authentication
            url = f"{settings.ZEROOPS_SERVER_URL}/v1/auth/login?state={self.auth_state}"
            webbrowser.open(url)
            
            # Update UI
            self.query_one("#login-btn", Button).disabled = True
            status_label = self.query_one("#status-label", Label)
            status_label.styles.display = "block"
            
            self.notify("Browser opened. Waiting for login...", severity="information")
            
            # Start polling
            self.set_interval(2.0, self.check_auth)

    async def check_auth(self) -> None:
        if not self.auth_state:
            return
            
        client = ZeroOpsClient()
        data = await client.poll_auth(self.auth_state)
        await client.close()
        
        if data.get("status") == "success":
            user_info = data.get("user", {})
            user_id = user_info.get("user_id")
            
            if user_id:
                self.notify(f"Authenticated as {user_id}!", severity="success")
                settings.USER_ID = user_id
                self.app.push_screen(Dashboard())



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

class Leaderboard(Screen):
    """Screen showing the leaderboard."""

    CSS = """
    Leaderboard {
        align: center middle;
    }
    
    #lb-container {
        width: 80%;
        height: 80%;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Global Leaderboard", classes="title"),
            DataTable(id="lb-table"),
            Button("Back", variant="primary", id="back"),
            id="lb-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Rank", width=5)
        table.add_column("User", width=15)
        table.add_column("XP", width=8)
        table.add_column("Level", width=6)
        
        client = ZeroOpsClient()
        data = await client.get_leaderboard()
        await client.close()
        
        # Populate table
        for i, entry in enumerate(data, 1):
             table.add_row(
                 str(i), 
                 entry.get("user_id"), 
                 str(entry.get("total_xp")),
                 str(entry.get("level"))
             )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

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

    #user-label {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
    }

    /* Level matches User color */
    #status-label {
        color: $accent;
    }
    
    /* Exercise is Red for visibility */
    #exercise-label {
        color: $error;
        text-style: italic;
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
        background: $surface;
        border: none;
        color: cyan;
        text-style: underline;
        margin: 0 2;
        min-width: 16;
        height: auto;
    }

    #actions Button:hover {
        color: deepskyblue;
        text-style: bold underline;
        background: $surface;
    }

    Markdown {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Top Bar with User Info
        yield Container(
            Label(f"User: {settings.USER_ID}", id="user-label"),
            Static("Level: ...", id="status-label", classes="stat"),
            Static("Exercise: ...", id="exercise-label", classes="stat"),
            id="top-bar"
        )

        # Main Subject Area (Big Container)
        yield ScrollableContainer(
            Markdown("Loading subject...", id="subject-md"),
            id="subject"
        )

        # Bottom Actions
        yield Container(
            Button("Submit", id="submit"),
            Button("Leaderboard", id="leaderboard"),
            Button("Quit", id="quit"),
            id="actions"
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
        data = await client.get_status()
        await client.close()
        
        if data.get("status") == "ok":
            self.query_one("#status-label", Static).update(f"Level: {data.get('current_level')}")
            ex_id = data.get('current_exercise')
            self.query_one("#exercise-label", Static).update(f"Exercise: {ex_id or 'None'}")
            self.current_exercise = ex_id
            
            if ex_id:
                client = ZeroOpsClient()
                details = await client.get_exercise_details(ex_id)
                await client.close()
                self.query_one("#subject-md", Markdown).update(details.get("subject", "No subject."))
                
                # Workspace Management
                # Create ~/rendudevops if not exists
                if not settings.RENDU_DIR.exists():
                     try:
                         settings.RENDU_DIR.mkdir(parents=True, exist_ok=True)
                         self.notify(f"Created workspace at {settings.RENDU_DIR}", severity="information")
                     except Exception as e:
                         self.notify(f"Could not create workspace: {e}", severity="error")

                # Create exercise dir
                ex_dir = settings.RENDU_DIR / ex_id
                if not ex_dir.exists():
                     try:
                         ex_dir.mkdir(exist_ok=True)
                         self.notify(f"Created directory for {ex_id}", severity="information")
                     except Exception as e:
                         self.notify(f"Could not create exercise dir: {e}", severity="error")

            else:
                 self.query_one("#subject-md", Markdown).update("No active exercise.")
        else:
            self.query_one("#status-label", Static).update(f"Error: {data.get('message', 'Unknown')}")

    async def submit_exercise(self):
        if not hasattr(self, "current_exercise") or not self.current_exercise:
            self.notify("No active exercise to submit!", severity="warning")
            return

        self.notify(f"Submitting {self.current_exercise}...", severity="information")
        
        # Get exercise details to determine file type
        client = ZeroOpsClient()
        details = await client.get_exercise_details(self.current_exercise)
        await client.close()
        
        exercise_type = details.get("type", "python")
        
        # Determine target files based on exercise type
        target_files = self._get_target_files(exercise_type)
        
        exercise_dir = settings.RENDU_DIR / self.current_exercise
        code_to_submit = ""
        files_found = []
        
        # Collect all matching files
        for target_file in target_files:
            file_path = exercise_dir / target_file
            if file_path.exists():
                files_found.append(target_file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        if code_to_submit:
                            code_to_submit += "\n---\n"  # YAML document separator
                        code_to_submit += content
                except Exception as e:
                    self.notify(f"Error reading {target_file}: {e}", severity="error")
                    return
        
        # Also check for any .yaml/.yml files in kubernetes exercises
        if exercise_type == "kubernetes":
            for yaml_file in exercise_dir.glob("*.yaml"):
                if yaml_file.name not in files_found:
                    files_found.append(yaml_file.name)
                    try:
                        with open(yaml_file, "r") as f:
                            content = f.read()
                            if code_to_submit:
                                code_to_submit += "\n---\n"
                            code_to_submit += content
                    except Exception as e:
                        self.notify(f"Error reading {yaml_file.name}: {e}", severity="error")
                        return
            for yml_file in exercise_dir.glob("*.yml"):
                if yml_file.name not in files_found:
                    files_found.append(yml_file.name)
                    try:
                        with open(yml_file, "r") as f:
                            content = f.read()
                            if code_to_submit:
                                code_to_submit += "\n---\n"
                            code_to_submit += content
                    except Exception as e:
                        self.notify(f"Error reading {yml_file.name}: {e}", severity="error")
                        return
        
        if not files_found:
            expected = ", ".join(target_files)
            self.notify(f"No files found. Expected: {expected}", severity="error")
            return
        
        client = ZeroOpsClient()
        data = await client.submit_exercise(self.current_exercise, code=code_to_submit)

        await client.close()
        
        is_success = data.get("status") == "success"
        message = data.get("message", "Unknown result")
        
        # Show detailed result in modal
        self.app.push_screen(SubmissionResultScreen(
            success=is_success,
            message=message,
            exercise_id=self.current_exercise
        ))
        
        if is_success:
            await self.refresh_status()

    def _get_target_files(self, exercise_type: str) -> list:
        """Return list of expected files based on exercise type."""
        file_mapping = {
            "python": ["main.py"],
            "docker": ["Dockerfile"],
            "kubernetes": [
                "deployment.yaml", "service.yaml", "pod.yaml", 
                "configmap.yaml", "secret.yaml", "ingress.yaml",
                "pv.yaml", "pvc.yaml", "namespace.yaml", "replicaset.yaml"
            ],
            "docker-compose": ["docker-compose.yaml", "docker-compose.yml"],
            "prometheus": ["prometheus.yml", "prometheus.yaml", "alerting-rules.yml"],
            "grafana": ["dashboard.json", "datasource.yaml"],
            "terraform": ["main.tf", "variables.tf", "outputs.tf"],
            "ansible": ["playbook.yaml", "playbook.yml", "inventory.ini"],
            "helm": ["Chart.yaml", "values.yaml"],
            "shell": ["script.sh", "main.sh"],
            "c": ["main.c", "Makefile"],
        }
        return file_mapping.get(exercise_type, ["main.py"])

