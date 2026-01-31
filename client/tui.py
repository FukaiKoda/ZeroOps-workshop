from __future__ import annotations

import argparse
import contextlib
import getpass
import io
import curses
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class TuiState:
    """Mutable UI state for the curses loop."""
    log: List[str]
    command: str = ""
    running: bool = True
    command_mode: bool = False


LOGO_PAIR = 1
LABEL_PAIR = 2


def _make_args(server: Optional[str], workspace: Optional[str], force: bool) -> argparse.Namespace:
    """Build a minimal argparse-like namespace for command handlers."""
    return argparse.Namespace(server=server, workspace=workspace, force=force)


def _run_action(func: Callable[[argparse.Namespace], None], args: argparse.Namespace) -> List[str]:
    """Run a command handler and capture its stdout/stderr as log lines."""
    output = io.StringIO()
    lines: List[str] = []
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            func(args)
        except Exception as exc:
            lines.append(f"ERROR: {exc}")
    text = output.getvalue().strip()
    if text:
        lines.extend(text.splitlines())
    return lines


def _load_ascii_art() -> List[str]:
    """Load ASCII art from ascii-art.txt in the repo root."""
    try:
        base = __file__
        art_path = Path(base).resolve().parents[1] / "ascii-art.txt"
        lines = art_path.read_text(encoding="utf-8").splitlines()
        return lines if lines else ["ZeroOps"]
    except Exception:
        return ["ZeroOps"]


def _draw(
    screen: curses.window,
    state: TuiState,
    username: str,
    workspace: Optional[str],
) -> None:
    """Render the TUI screen."""
    screen.erase()
    height, width = screen.getmaxyx()
    title = "ZeroOps Client TUI"
    blue = curses.color_pair(LOGO_PAIR) | curses.A_BOLD
    label = curses.color_pair(LABEL_PAIR) | curses.A_BOLD
    logo_lines = _load_ascii_art()
    header_height = len(logo_lines)
    start_row = 0
    def safe_addstr(row: int, col: int, text: str, attr: int | None = None) -> None:
        """Safely write text within screen bounds."""
        if row < 0 or row >= height:
            return
        if col < 0 or col >= width:
            return
        max_len = max(0, width - col)
        snippet = text[:max_len]
        if not snippet:
            return
        if attr is None:
            screen.addstr(row, col, snippet)
        else:
            screen.addstr(row, col, snippet, attr)

    max_logo_width = max((len(line) for line in logo_lines), default=0)
    x_offset = max(0, (width - max_logo_width) // 2)

    for idx, line in enumerate(logo_lines):
        row = start_row + idx
        if row >= height:
            break
        truncated = line[: max(0, width - x_offset)]
        safe_addstr(row, x_offset, truncated, blue)

    title_row = min(height - 1, header_height)
    safe_addstr(title_row, max(0, (width - len(title)) // 2), title, curses.A_BOLD)

    info_row = title_row + 2
    safe_addstr(info_row, 2, f'Logging in as "{username}"', label)
    safe_addstr(info_row + 1, 2, f"Workspace: {workspace or '~'} (zeroops/)", label)
    safe_addstr(info_row + 3, 2, "Commands: sync, subject, grademe, status, quit", label)
    safe_addstr(info_row + 4, 2, "Press ':' to enter command mode, then Enter.", label)

    log_start = info_row + 6
    max_log_lines = max(0, height - log_start - 3)
    log_lines = state.log[-max_log_lines:]
    safe_addstr(log_start - 1, 2, "Output:")
    for idx, line in enumerate(log_lines):
        truncated = line[: max(0, width - 4)]
        safe_addstr(log_start + idx, 2, truncated)

    footer = "Command mode: ':'  |  Commands: sync subject grademe status quit"
    safe_addstr(height - 2, 2, footer[: max(0, width - 4)], label)
    prompt = f":{state.command}" if state.command_mode else ">"
    safe_addstr(height - 1, 2, prompt[: max(0, width - 4)])
    screen.refresh()


def run_tui(server: Optional[str], workspace: Optional[str], force: bool) -> None:
    """Run the interactive TUI loop."""
    try:
        from client.client import cmd_correct, cmd_status, cmd_subject, cmd_sync
    except ImportError:  # pragma: no cover
        from client import cmd_correct, cmd_status, cmd_subject, cmd_sync  # type: ignore

    username = getpass.getuser()
    state = TuiState(log=[f'Logging in as "{username}"', "TUI started. Press ':' to enter command mode."])
    args = _make_args(server, workspace, force)

    def loop(screen: curses.window) -> None:
        """Main curses loop for rendering and input handling."""
        curses.start_color()
        curses.use_default_colors()
        try:
            if curses.can_change_color() and curses.COLORS >= 16:
                color_id = min(10, curses.COLORS - 1)
                # #238DE0 -> RGB in 0-1000 range
                curses.init_color(color_id, 137, 553, 878)
                curses.init_pair(LOGO_PAIR, color_id, -1)
                curses.init_pair(LABEL_PAIR, color_id, -1)
            else:
                curses.init_pair(LOGO_PAIR, curses.COLOR_BLUE, -1)
                curses.init_pair(LABEL_PAIR, curses.COLOR_BLUE, -1)
        except Exception:
            curses.init_pair(LOGO_PAIR, curses.COLOR_BLUE, -1)
            curses.init_pair(LABEL_PAIR, curses.COLOR_BLUE, -1)
        curses.curs_set(1)
        screen.nodelay(False)
        while state.running:
            _draw(screen, state, username, workspace)
            ch = screen.getch()
            if ch == ord(":"):
                state.command_mode = True
                state.command = ""
            elif ch in (27,):  # ESC
                state.command_mode = False
                state.command = ""
            elif ch in (curses.KEY_ENTER, 10, 13):
                if state.command_mode:
                    cmd = state.command.strip().lower()
                    state.command = ""
                    state.command_mode = False
                    if cmd:
                        _handle_command(cmd, args, state)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if state.command_mode and state.command:
                    state.command = state.command[:-1]
            elif 32 <= ch <= 126:
                if state.command_mode:
                    state.command += chr(ch)

    def _help_lines() -> List[str]:
        """Return formatted help lines for the TUI command list."""
        return [
            "Commands:",
            "  sync (s)       - sync current level and subject",
            "  subject (sub)  - fetch subject only",
            "  grademe (g)    - run local tests and submit",
            "  status (st)    - show status",
            "  quit (q)       - exit TUI",
            "  help (h)       - show this help",
        ]

    def _handle_command(command: str, args_ns: argparse.Namespace, state_obj: TuiState) -> None:
        """Dispatch a user command string to the appropriate action."""
        if not command:
            return
        cmd = command.split()[0]
        if cmd in {"sync", "s"}:
            state_obj.log.extend(_run_action(cmd_sync, args_ns))
        elif cmd in {"subject", "sub"}:
            state_obj.log.extend(_run_action(cmd_subject, args_ns))
        elif cmd in {"grademe", "correct", "g"}:
            state_obj.log.extend(_run_action(cmd_correct, args_ns))
        elif cmd in {"status", "st"}:
            state_obj.log.extend(_run_action(cmd_status, args_ns))
        elif cmd in {"quit", "exit", "q"}:
            state_obj.running = False
        elif cmd in {"help", "h"}:
            state_obj.log.extend(_help_lines())
        else:
            state_obj.log.append(f"Unknown command: {command}")

    curses.wrapper(loop)
