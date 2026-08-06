"""
Main dashboard screen.

Displays:
  - GitHub avatar (emoji placeholder in TUI) and username
  - Linked repository name + last sync info
  - Current exercise subject (Markdown)
  - Exercise status: Not Started | In Progress | Passed | Failed
  - Progress percentage
  - Buttons: Submit, Sync Repository, Leaderboard, Quit
"""

import webbrowser
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Label, Header, Footer, Static, Markdown

from api.client import ZeroOpsClient
from utils.config import settings

from .modals import QuitScreen, SubmissionResultScreen
from .leaderboard import Leaderboard


class Dashboard(Screen):
    """Main dashboard showing user progress, GitHub identity and repository state."""

    CSS = """
    Dashboard {
        layout: vertical;
        width: 100%;
        height: 100%;
    }

    /* Top identity bar */
    #top-bar {
        height: auto;
        width: 100%;
        padding: 1 2;
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 1fr;
        margin-bottom: 0;
        border-bottom: solid $primary;
    }

    .stat-col {
        layout: vertical;
        height: auto;
    }

    .stat {
        color: $text-muted;
        margin-bottom: 0;
    }

    .stat-value {
        text-style: bold;
        margin-bottom: 0;
    }

    #username-label {
        color: $accent;
        text-style: bold;
    }

    #repo-label {
        color: $success;
        text-style: bold;
    }

    #sync-info-label {
        color: $text-muted;
    }

    #commit-label {
        color: $text-muted;
    }

    /* Progress bar row */
    #progress-bar {
        height: 3;
        width: 100%;
        padding: 0 2;
        layout: horizontal;
        margin-bottom: 0;
    }

    #progress-label {
        width: 1fr;
        content-align: left middle;
        color: $primary;
    }

    #exercise-status-label {
        width: auto;
        content-align: right middle;
        padding: 0 1;
    }

    /* Subject area */
    #subject {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        margin: 0;
        padding: 1 2;
        min-height: 10;
    }

    /* Action row */
    #actions {
        height: 5;
        align: center middle;
        layout: horizontal;
        padding-bottom: 1;
        width: 100%;
        border-top: solid $primary;
    }

    #actions Button {
        margin: 0 1;
        min-width: 18;
    }

    #sync-btn {
        color: $success;
    }

    Markdown {
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_exercise: str | None = None
        self._last_commit_hash: str | None = None

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        if event.href:
            self.notify(f"Opening {event.href}...", severity="information")
            webbrowser.open(event.href)

    def compose(self) -> ComposeResult:
        yield Header()

        # Identity + repo card (2-column grid)
        yield Container(
            Container(
                Static("👤 GitHub", classes="stat"),
                Static("@...", id="username-label", classes="stat-value"),
                Static("Level: ...", id="status-label", classes="stat-value"),
                Static("XP: ...", id="xp-label", classes="stat"),
                classes="stat-col",
            ),
            Container(
                Static("📁 Repository", classes="stat"),
                Static("—", id="repo-label", classes="stat-value"),
                Static("Last sync: —", id="sync-info-label", classes="stat"),
                Static("Commit: —", id="commit-label", classes="stat"),
                classes="stat-col",
            ),
            id="top-bar",
        )

        # Progress row
        yield Container(
            Static("Exercise: loading...", id="progress-label"),
            Static("", id="exercise-status-label"),
            id="progress-bar",
        )

        # Exercise subject
        yield ScrollableContainer(
            Markdown("Loading...", id="subject-md"), id="subject"
        )

        # Actions
        yield Container(
            Button("Submit", variant="primary", id="submit"),
            Button("🔄 Sync Repository", variant="default", id="sync-btn"),
            Button("Leaderboard", variant="primary", id="leaderboard"),
            Button("Quit", variant="error", id="quit"),
            id="actions",
        )

        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_status()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "quit":
                self.app.push_screen(QuitScreen())
            case "submit":
                await self.submit_exercise()
            case "sync-btn":
                await self.sync_repository()
            case "leaderboard":
                self.app.push_screen(Leaderboard())

    # -----------------------------------------------------------------------
    # Status refresh
    # -----------------------------------------------------------------------

    async def refresh_status(self) -> None:
        """Fetch profile + status + exercise details and update all widgets."""
        client = ZeroOpsClient()
        try:
            # Fetch GitHub profile and repo info
            me = await client.get_me()
            if "github_username" not in me:
                self._show_error("Session expired. Please restart and log in again.")
                await client.close()
                return

            settings.USER_ID = me["github_username"]
            self._update_identity(me)

            # Fetch exercise status
            data = await client.get_status()
        except Exception as e:
            self.notify(f"Connection error: {e}", severity="error")
            await client.close()
            return
        finally:
            await client.close()

        if data.get("status") == "ok":
            level = data.get("current_level", 0)
            ex_id = data.get("current_exercise")

            self.query_one("#status-label", Static).update(f"Level: {level}")
            self.current_exercise = ex_id

            if ex_id:
                folder_name = await self._load_exercise_subject(ex_id)
                folder_disp = folder_name or ex_id
                self.query_one("#progress-label", Static).update(
                    f"Exercise: {ex_id}  •  Target Folder: {folder_disp}/"
                )
                self._ensure_workspace_ready(folder_disp)
                await self._update_exercise_status(ex_id)
            else:
                self.query_one("#progress-label", Static).update(
                    "🎉 All exercises complete!"
                )
                self.query_one("#subject-md", Markdown).update(
                    "**Congratulations!** You have completed all exercises."
                )
        else:
            self._show_error(data.get("message", "Unknown error"))

    def _update_identity(self, me: dict) -> None:
        """Update GitHub identity and repo widgets from profile data."""
        username = me.get("github_username", "—")
        avatar = me.get("github_avatar", "")  # URL, not displayable in TUI
        level = me.get("current_level", 0)
        xp = me.get("total_xp", 0)

        self.query_one("#username-label", Static).update(f"@{username}")
        self.query_one("#status-label", Static).update(f"Level: {level}")
        self.query_one("#xp-label", Static).update(f"XP: {xp}")

        repo = me.get("repository")
        if repo:
            full_name = repo.get("full_name", "—")
            last_commit = repo.get("last_commit_hash")
            last_sync = repo.get("last_synced_at")

            self.query_one("#repo-label", Static).update(f"📁 {full_name}")

            if last_sync:
                # Show a compact timestamp
                sync_str = last_sync[:19].replace("T", " ") if last_sync else "Never"
                self.query_one("#sync-info-label", Static).update(
                    f"Last sync: {sync_str}"
                )
            else:
                self.query_one("#sync-info-label", Static).update("Last sync: Never")

            if last_commit:
                self._last_commit_hash = last_commit
                short = last_commit[:7]
                self.query_one("#commit-label", Static).update(f"Commit: {short}")
            else:
                self.query_one("#commit-label", Static).update("Commit: —")
        else:
            self.query_one("#repo-label", Static).update("No repository linked")
            self.query_one("#sync-info-label", Static).update("")
            self.query_one("#commit-label", Static).update("")

    async def _load_exercise_subject(self, ex_id: str) -> str:
        """Fetch and render the exercise markdown subject. Returns the folder name."""
        client = ZeroOpsClient()
        folder_name = ex_id
        try:
            details = await client.get_exercise_details(ex_id)
            folder_name = details.get("folder") or ex_id
            subject_md = details.get("subject", "No subject available.")
            header_prefix = f"> **Target Directory in Portfolio Repository:** `{folder_name}/`\n\n---\n\n"
            self.query_one("#subject-md", Markdown).update(header_prefix + subject_md)
        except Exception as e:
            self.notify(f"Failed to load exercise details: {e}", severity="error")
        finally:
            await client.close()
        return folder_name

    async def _update_exercise_status(self, ex_id: str) -> None:
        """Fetch submission history and set the status badge for the current exercise."""
        client = ZeroOpsClient()
        try:
            submissions = await client.get_submissions()
        except Exception:
            submissions = []
        finally:
            await client.close()

        status_label = self.query_one("#exercise-status-label", Static)

        # Find the most recent submission for this exercise
        exercise_subs = [s for s in submissions if s.get("exercise_id") == ex_id]
        if not exercise_subs:
            status_label.update("🟡 In Progress")
            status_label.styles.color = "yellow"
        else:
            latest = exercise_subs[0]  # Already sorted desc by submitted_at
            status = latest.get("status", "")
            if status == "passed":
                status_label.update("✅ Passed")
                status_label.styles.color = "green"
            elif status == "failed":
                status_label.update("❌ Failed")
                status_label.styles.color = "red"
            else:
                status_label.update("🟡 In Progress")
                status_label.styles.color = "yellow"

    def _ensure_workspace_ready(self, folder_name: str) -> None:
        """Ensure local workspace directory exists for exercise folder."""
        if not settings.RENDU_DIR.exists():
            try:
                settings.RENDU_DIR.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.notify(f"Could not create workspace: {e}", severity="error")

        ex_dir = settings.RENDU_DIR / folder_name
        if not ex_dir.exists():
            try:
                ex_dir.mkdir(exist_ok=True)
                self.notify(f"Created directory for {folder_name}", severity="information")
            except Exception as e:
                self.notify(f"Could not create exercise dir: {e}", severity="error")


    def _show_error(self, message: str) -> None:
        try:
            self.query_one("#progress-label", Static).update(f"⚠ {message}")
        except Exception:
            self.notify(message, severity="error")

    # -----------------------------------------------------------------------
    # Sync
    # -----------------------------------------------------------------------

    async def sync_repository(self) -> None:
        """Trigger a repository sync and refresh the dashboard."""
        sync_btn = self.query_one("#sync-btn", Button)
        sync_btn.disabled = True
        self.notify("Syncing repository...", severity="information")

        client = ZeroOpsClient()
        try:
            result = await client.sync_repo()
        except Exception as e:
            result = {"status": "error", "message": str(e)}
        finally:
            await client.close()
            sync_btn.disabled = False

        status = result.get("status")
        if status == "synced":
            commit = result.get("commit_hash", "")
            short = commit[:7] if commit else "—"
            folders = result.get("exercise_folders", [])
            self._last_commit_hash = commit or self._last_commit_hash
            self.notify(
                f"Synced! Latest commit: {short}  •  {len(folders)} folder(s) found",
                severity="success",
                timeout=5,
            )
            # Refresh to show updated sync info
            await self.refresh_status()
        else:
            message = result.get("message", "Sync failed.")
            self.notify(f"Sync failed: {message}", severity="error")

    # -----------------------------------------------------------------------
    # Submit
    # -----------------------------------------------------------------------

    async def submit_exercise(self) -> None:
        if not self.current_exercise:
            self.notify("No active exercise to submit!", severity="warning")
            return

        self.notify(f"Submitting {self.current_exercise}...", severity="information")

        # Fetch exercise type to determine collection strategy
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

        # ---------------------------------------------------------------
        # GitHub Actions: server fetches workflow files from GitHub API.
        # No local file reading needed.
        # ---------------------------------------------------------------
        if exercise_type == "github_actions":
            client = ZeroOpsClient()
            try:
                data = await client.submit_exercise(
                    self.current_exercise,
                    code="",  # server ignores this for github_actions
                    commit_hash=self._last_commit_hash,
                )
            except Exception as e:
                self.notify(f"Submission failed: {e}", severity="error")
                return
            finally:
                await client.close()

            is_success = data.get("status") == "success"
            message = data.get("message", "Unknown result")

            async def _on_result_dismissed_ga(dismissed_result=None) -> None:
                await self.refresh_status()

            self.app.push_screen(
                SubmissionResultScreen(
                    success=is_success,
                    message=message,
                    exercise_id=self.current_exercise,
                ),
                _on_result_dismissed_ga,
            )
            return

        # ---------------------------------------------------------------
        # All other exercise types: collect local files, run locally
        # ---------------------------------------------------------------
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
                self.current_exercise,
                code=code_to_submit,
                commit_hash=self._last_commit_hash,
            )
        except Exception as e:
            self.notify(f"Submission failed: {e}", severity="error")
            await client.close()
            return
        finally:
            await client.close()

        is_success = data.get("status") == "success"
        message = data.get("message", "Unknown result")

        async def _on_result_dismissed(dismissed_result=None) -> None:
            await self.refresh_status()

        self.app.push_screen(
            SubmissionResultScreen(
                success=is_success,
                message=message,
                exercise_id=self.current_exercise,
            ),
            _on_result_dismissed,
        )

    # -----------------------------------------------------------------------
    # File helpers (unchanged from original)
    # -----------------------------------------------------------------------

    def _collect_exercise_code(
        self, exercise_dir, target_files, exercise_type
    ) -> tuple[str, list]:
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

        if exercise_type == "github_actions":
            workflows_dir = exercise_dir / ".github" / "workflows"
            if workflows_dir.exists():
                for ext in ["*.yaml", "*.yml"]:
                    for fpath in workflows_dir.glob(ext):
                        rel_name = f".github/workflows/{fpath.name}"
                        if rel_name not in files_found:
                            files_found.append(rel_name)
                            content = read_file(fpath)
                            if content is not None:
                                code_parts.append(content)

        return "\n---\n".join(code_parts), files_found

    def _get_target_files(self, exercise_type: str) -> list:
        file_mapping = {
            "python": ["main.py"],
            "docker": ["Dockerfile"],
            "kubernetes": [
                "deployment.yaml", "service.yaml", "pod.yaml",
                "configmap.yaml", "secret.yaml", "ingress.yaml",
                "pv.yaml", "pvc.yaml", "namespace.yaml", "replicaset.yaml",
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
            "github_actions": [
                ".github/workflows/build.yml",
                ".github/workflows/build.yaml",
                ".github/workflows/ci.yml",
                ".github/workflows/ci.yaml",
                ".github/workflows/main.yml",
                ".github/workflows/main.yaml",
            ],
        }
        return file_mapping.get(exercise_type, ["main.py"])
