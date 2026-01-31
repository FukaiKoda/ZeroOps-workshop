from textual.app import ComposeResult
from textual.containers import Grid, Container, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Label, Header, Footer, Static, Markdown, DataTable
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
                id="subject"
            ),
            Container(
                Button("Refresh", variant="primary", id="refresh"),
                Button("Submit", variant="success", id="submit"),
                Button("Leaderboard", variant="warning", id="leaderboard"),
                Button("Quit", variant="error", id="quit"),
                id="actions"
            ),
            id="info-container"
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
        elif event.button.id == "leaderboard":
            self.app.push_screen(Leaderboard())

    async def refresh_status(self):
        client = ZeroOpsClient()
        data = await client.get_status()
        await client.close()
        
        if data.get("status") == "ok":
            self.query_one("#status-label", Static).update(f"Level: {data.get('current_level')}")
            ex_id = data.get('current_exercise')
            self.query_one("#exercise-label", Static).update(f"Current Exercise: {ex_id or 'None'}")
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
        
        # Determine code to submit based on exercise
        target_file = "main.py" 
        if self.current_exercise == "ex01_docker":
             target_file = "Dockerfile"
        
        file_path = settings.RENDU_DIR / self.current_exercise / target_file
        
        if not file_path.exists():
            self.notify(f"Missing file: {target_file} in {self.current_exercise}", severity="error")
            return

        try:
            with open(file_path, "r") as f:
                code_to_submit = f.read()
        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")
            return
        
        client = ZeroOpsClient()
        data = await client.submit_exercise(self.current_exercise, code=code_to_submit)

        await client.close()
        
        if data.get("status") == "success":
            self.notify(f"Success! {data.get('message')}", severity="information")
            await self.refresh_status()
        else:
            self.notify(f"Failed: {data.get('message')}", severity="error")

