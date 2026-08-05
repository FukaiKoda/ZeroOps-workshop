from textual.app import ComposeResult
from textual.containers import Container, Center
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer
from api.client import ZeroOpsClient


class LeaderboardCard(Container):
    """A card for a single leaderboard entry."""

    def __init__(self, rank: int, github_username: str, xp: int, level: int):
        super().__init__()
        self.rank = rank
        self.github_username = github_username
        self.xp = xp
        self.level = level

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
        yield Label(f"#{self.rank}", classes="lb-rank")

        icon = ""
        if self.rank == 1:
            icon = "👑"
        elif self.rank == 2:
            icon = "🥈"
        elif self.rank == 3:
            icon = "🥉"

        if icon:
            yield Label(icon, classes="crown")

        yield Center(Label("👤", classes="lb-avatar"))

        yield Label(f"@{self.github_username}", classes="lb-user")

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
        yield Header()
        yield Container(
            Container(
                Button("← Back", variant="default", id="back-btn"), id="lb-header"
            ),
            Label("Global Leaderboard", classes="title"),
            Container(id="podium"),
            Container(id="rest-list"),
            id="lb-container",
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

        top_3 = data[:3]
        others = data[3:]

        podium_entries = []
        if len(top_3) >= 1:
            podium_entries.append((1, top_3[0]))
        if len(top_3) >= 2:
            podium_entries.append((2, top_3[1]))
        if len(top_3) >= 3:
            podium_entries.append((3, top_3[2]))

        visual_order = []
        r2 = next((x for x in podium_entries if x[0] == 2), None)
        if r2:
            visual_order.append(r2)

        r1 = next((x for x in podium_entries if x[0] == 1), None)
        if r1:
            visual_order.append(r1)
        r3 = next((x for x in podium_entries if x[0] == 3), None)
        if r3:
            visual_order.append(r3)

        for rank, entry in visual_order:
            podium.mount(
                LeaderboardCard(
                    rank=rank,
                    github_username=entry.get("github_username", entry.get("user_id", "?")),
                    xp=entry.get("total_xp"),
                    level=entry.get("level"),
                )
            )

        for i, entry in enumerate(others, 4):
            rest_list.mount(
                LeaderboardCard(
                    rank=i,
                    github_username=entry.get("github_username", entry.get("user_id", "?")),
                    xp=entry.get("total_xp"),
                    level=entry.get("level"),
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("back", "back-btn"):
            self.app.pop_screen()
