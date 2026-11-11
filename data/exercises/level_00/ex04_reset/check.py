import subprocess
from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex04_reset (Lab 05: Time Travel).

    Evaluates 3 distinct parts:
      - Part 1: progress.txt exists in the repository
      - Part 2: progress.txt contains all three steps (step 1, step 2, step 3)
      - Part 3: Working tree is clean and commits are intact
    """
    exercise_path = exercise_path.expanduser().resolve()
    git_dir = _find_git_dir(exercise_path)

    # --- Part 1: Locate progress.txt ---
    progress_files = list(exercise_path.rglob("progress.txt"))
    if not progress_files:
        if "progress.txt" in code and "step" in code:
            progress_content = code
        else:
            return (
                False,
                "[Part 1 Failed] progress.txt not found. Work inside ~/rendudevops/ex04_reset/lab05/.",
            )
    else:
        progress_content = progress_files[0].read_text()

    # --- Part 2: Verify all 3 steps restored ---
    lines = [l.strip() for l in progress_content.splitlines() if l.strip().startswith("step")]
    # Also handle general lines
    all_lines = [l.strip() for l in progress_content.splitlines() if l.strip()]

    if len(lines) < 3 and len(all_lines) < 3:
        return (
            False,
            f"[Part 2 Failed] progress.txt only has {len(lines)} step(s). Use 'git reflog' and 'git reset --hard HEAD@{{1}}' to restore all 3 steps.",
        )

    for step_num in ["1", "2", "3"]:
        expected = f"step {step_num}"
        if not any(expected in l for l in all_lines):
            return (
                False,
                f"[Part 2 Failed] progress.txt is missing '{expected}'. All three steps must be present.",
            )

    # --- Part 3: Verify Git Repository State (if present) ---
    if git_dir and git_dir.exists():
        repo_dir = git_dir.parent
        try:
            log_res = subprocess.run(
                ["git", "-C", str(repo_dir), "log", "--oneline"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            commit_count = len(log_res.stdout.strip().splitlines())
            if commit_count < 3:
                return (
                    False,
                    f"[Part 3 Failed] Repository only shows {commit_count} commit(s). Restore the 3rd commit from reflog.",
                )
        except Exception:
            pass

    return (
        True,
        "All parts passed: [Part 1: progress.txt Found OK] [Part 2: All 3 Steps Restored OK] [Part 3: Git History OK]",
    )


def _find_git_dir(start_path: Path) -> Path | None:
    """Locate the .git directory either directly or via known exercise files."""
    if (start_path / ".git").exists():
        return start_path / ".git"

    known_files = ["progress.txt"]
    for known in known_files:
        found = list(start_path.rglob(known))
        if found:
            candidate = found[0].parent / ".git"
            if candidate.exists():
                return candidate

    current = start_path
    while current.parent != current:
        if (current / ".git").exists():
            return current / ".git"
        current = current.parent

    return None
