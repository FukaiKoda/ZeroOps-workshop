from textual.app import ComposeResult
from textual.containers import Grid, Container, Vertical, ScrollableContainer, Center
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
            self.poll_timer = self.set_interval(2.0, self.check_auth)

    async def check_auth(self) -> None:
        if not self.auth_state:
            return
            
        client = ZeroOpsClient()
        try:
            data = await client.poll_auth(self.auth_state)
        except Exception:
            # Silently ignore polling errors
            await client.close()
            return
        
        await client.close()
        
        if data.get("status") == "success":
            user_info = data.get("user", {})
            user_id = user_info.get("user_id")
            
            if user_id:
                self.notify(f"Authenticated as {user_id}!", severity="success")
                settings.USER_ID = user_id
                
                # Stop polling
                if hasattr(self, "poll_timer"):
                    self.poll_timer.stop()
                self.auth_state = ""
                
                # Switch to Dashboard (replaces LoginScreen)
                self.app.switch_screen(Dashboard())



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

class LeaderboardCard(Container):
    """A card for a single leaderboard entry."""
    
    def __init__(self, rank: int, user_id: str, xp: int, level: int):
        super().__init__()
        self.rank = rank
        self.user_id = user_id
        self.xp = xp
        self.level = level
        
        # Determine classes based on rank
        self.add_class("lb-card")
        if rank == 1:
            self.add_class("rank-1")
        elif rank == 2:
            self.add_class("rank-2")
        elif rank == 3:
            self.add_class("rank-3")
        else:
            self.add_class("rank-other")

    def compose(self) -> ComposeResult:
        # Rank badge
        yield Label(f"#{self.rank}", classes="lb-rank")
        
        # Rank Icons
        icon = ""
        if self.rank == 1:
            icon = "👑"
        elif self.rank == 2:
            icon = "🥈"
        elif self.rank == 3:
            icon = "🥉"
            
        if icon:
            yield Label(icon, classes="crown")

        # Avatar (Placeholder for TUI)
        # Using a large character or ASCII art. 
        # Ideally we would fetch and render the image using a library, but for stability in a standard TUI:
        yield Center(Label("👤", classes="lb-avatar")) 
        
        # User Info
        yield Label(f"{self.user_id}", classes="lb-user")
        
        yield Label(f"{self.xp} XP", classes="lb-xp")
        yield Label(f"Level {self.level}", classes="lb-level")


class Leaderboard(Screen):
    """Screen showing the leaderboard with a visual layout."""

    CSS = """
    Leaderboard {
        align: center middle;
    }
    
    #lb-container {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 1 2;
        background: $surface;
        overflow-y: auto;
    }
    
    #lb-header {
        width: 100%;
        height: 3;
        align: left middle;
    }

    #back-btn {
        width: auto;
        border: none;
        background: $surface;
        color: $error;
        text-style: underline;
        min-width: 10;
        height: 1;
    }
    
    .title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        content-align: center middle; 
    }
    
    /* Podium Layout for Top 3 */
    #podium {
        layout: horizontal;
        height: 25;
        width: 100%;
        align: center bottom;
        margin-bottom: 2;
    }

    /* Grid for the rest */
    #rest-list {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1;
        width: 100%;
        height: auto;
    }
    
    /* Card Styling */
    .lb-card {
        layout: vertical;
        border: solid $primary;
        background: $surface;
        padding: 1;
        height: 18;
        width: 100%;
        align: center middle;
    }
    
    .lb-rank {
        background: $primary;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
        text-style: bold;
    }
    
    .lb-avatar {
        text-align: center;
        color: $accent;
        margin: 0 0 1 0;
        text-style: bold;
        border: round $accent;
        padding: 1 2;
        height: 5;
        width: 10;
        content-align: center middle;
    }
    
    .lb-user {
        width: 100%;
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 0;
    }
    
    .lb-xp {
        width: 100%;
        text-align: center;
        color: white;
        text-style: bold;
    }
    
    .lb-level {
        width: 100%;
        text-align: center;
        color: $text-muted;
    }
    
    /* Top 3 Specifics */
    .rank-1 {
        border: double gold;
        height: 22;
        width: 30;
        margin: 0 2;
        background: #1a1a00;
    }
    
    .rank-1 .lb-rank {
        background: gold;
        color: black;
    }
    .rank-1 .lb-avatar { border: round gold; color: gold; }
    .rank-1 .crown { display: block; color: gold; margin-bottom: 1; }
    
    .rank-2 {
        border: heavy silver;
        height: 20;
        width: 25;
        margin-top: 2;
        background: #1a1a1a;
    }
    
    .rank-2 .lb-rank { background: silver; color: black; }
    .rank-2 .lb-avatar { border: round silver; color: silver; }
    .rank-2 .crown { display: block; color: silver; margin-bottom: 1; }
    
    .rank-3 {
        border: heavy #cd7f32; /* Bronze */
        height: 20;
        width: 25;
        margin-top: 2;
        background: #1a0d00;
    }
    
    .rank-3 .lb-rank { background: #cd7f32; color: black; }
    .rank-3 .lb-avatar { border: round #cd7f32; color: #cd7f32; }
    .rank-3 .crown { display: block; color: #cd7f32; margin-bottom: 0; }
    
    .crown { 
        display: none; 
        width: 100%;
        text-align: center;
    }
    
    .rank-other {
        height: 14;
    }
    
    #back-btn-container {
        width: 100%;
        align: center bottom;
        margin-top: 2;
        height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        # yield Header() # Optional: keeping or removing based on preference, but user focused on "Global Leaderboard" title placement.
        # I will keep Header() as it is standard, but my custom header is below it.
        yield Header() 
        yield Container(
            Container(
                Button("← Back", variant="default", id="back-btn"),
                id="lb-header"
            ),
            Label("Global Leaderboard", classes="title"),
            Container(id="podium"),
            Container(id="rest-list"),
            id="lb-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        podium = self.query_one("#podium")
        rest_list = self.query_one("#rest-list")
        
        client = ZeroOpsClient()
        try:
            data = await client.get_leaderboard()
        except Exception as e:
            self.notify(f"Failed to load leaderboard: {e}", severity="error")
            data = []
        finally:
            await client.close()
        
        # Sort so that rank 1 is in middle for visual podium
        # Data is already sorted by rank 1..N
        
        # Top 3
        top_3 = data[:3]
        others = data[3:]
        
        # Create Podium Cards
        # We want order: 2, 1, 3 for visual effect (Left, Center, Right)
        # But we can control this with 'order' in CSS or insertion order.
        # CSS 'order' property is not fully supported in Textual for `Horizontal` layout same as Flexbox without specific enabled flags sometimes?
        # Textual supports `dock` or just insertion order.
        # Let's insert them in order: 2, 1, 3.
        
        podium_entries = []
        if len(top_3) >= 1: podium_entries.append((1, top_3[0]))
        if len(top_3) >= 2: podium_entries.append((2, top_3[1]))
        if len(top_3) >= 3: podium_entries.append((3, top_3[2]))
        
        # Reorder for visual: 2, 1, 3
        visual_order = []
        # Find rank 2
        r2 = next((x for x in podium_entries if x[0] == 2), None)
        if r2: visual_order.append(r2)
        
        # Find rank 1
        r1 = next((x for x in podium_entries if x[0] == 1), None)
        if r1: visual_order.append(r1)
        
        # Find rank 3
        r3 = next((x for x in podium_entries if x[0] == 3), None)
        if r3: visual_order.append(r3)
        
        for rank, entry in visual_order:
            podium.mount(LeaderboardCard(
                rank=rank,
                user_id=entry.get("user_id"),
                xp=entry.get("total_xp"),
                level=entry.get("level")
            ))
            
        # Others
        for i, entry in enumerate(others, 4):
             rest_list.mount(LeaderboardCard(
                rank=i,
                user_id=entry.get("user_id"),
                xp=entry.get("total_xp"),
                level=entry.get("level")
            ))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("back", "back-btn"):
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

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Top Bar with User Info
        yield Container(
            Label(f"User: {settings.USER_ID}", id="user-label"),
            Static("Level: ...", id="status-label", classes="stat"),
            Static("Exercise: ...", id="exercise-label", classes="stat"),
            Static("Rendu: ...", id="rendu-label", classes="stat"),
            id="top-bar"
        )

        # Main Subject Area (Big Container)
        yield ScrollableContainer(
            Markdown("Loading subject...", id="subject-md"),
            id="subject"
        )

        # Bottom Actions
        yield Container(
            Button("Submit", variant="primary", id="submit"),
            Button("Leaderboard", variant="primary", id="leaderboard"),
            Button("Quit", variant="primary", id="quit"),
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
        try:
            data = await client.get_status()
        except Exception as e:
            self.notify(f"Connection error: {e}", severity="error")
            data = {"status": "error", "message": "Failed to connect to server."}
        finally:
            await client.close()
        
        if data.get("status") == "ok":
            self.query_one("#status-label", Static).update(f"Level: {data.get('current_level')}")
            ex_id = data.get('current_exercise')
            self.query_one("#exercise-label", Static).update(f"Exercise: {ex_id or 'None'}")
            self.query_one("#rendu-label", Static).update(f"Rendu: ~/rendudevops/{ex_id or '...'}")
            self.current_exercise = ex_id
            
            if ex_id:
                client = ZeroOpsClient()
                try:
                    details = await client.get_exercise_details(ex_id)
                except Exception as e:
                    self.notify(f"Failed to load exercise details: {e}", severity="error")
                    details = {}
                finally:
                    await client.close()
                
                self.query_one("#subject-md", Markdown).update(details.get("subject", "No subject."))
                
                self._ensure_workspace_ready(ex_id)
            else:
                 self.query_one("#subject-md", Markdown).update("No active exercise.")
        else:
            self.query_one("#status-label", Static).update(f"Error: {data.get('message', 'Unknown')}")

    def _ensure_workspace_ready(self, ex_id: str) -> None:
        """Ensure local workspace directories exist."""
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

    def _collect_exercise_code(self, exercise_dir, target_files, exercise_type) -> tuple[str, list]:
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

        # 1. Target files
        for target in target_files:
            file_path = exercise_dir / target
            if file_path.exists():
                files_found.append(target)
                content = read_file(file_path)
                if content is not None:
                     code_parts.append(content)

        # 2. Kubernetes wildcards
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
        
        # Get exercise details to determine file type
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
        
        # Determine target files based on exercise type
        target_files = self._get_target_files(exercise_type)
        
        exercise_dir = settings.RENDU_DIR / self.current_exercise
        
        code_to_submit, files_found = self._collect_exercise_code(exercise_dir, target_files, exercise_type)
        
        if target_files and not files_found:
            expected = ", ".join(target_files)
            self.notify(f"No files found. Expected: {expected}", severity="error")
            return
        
        client = ZeroOpsClient()
        try:
            data = await client.submit_exercise(self.current_exercise, code=code_to_submit)
        except Exception as e:
            self.notify(f"Submission failed: {e}", severity="error")
            return
        finally:
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
            "interactive": [],
        }
        return file_mapping.get(exercise_type, ["main.py"])

