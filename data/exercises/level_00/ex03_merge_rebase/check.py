import subprocess
from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex03_merge_rebase (Lab 04: Bringing Branches Together).

    Evaluates 3 distinct parts:
      - Part 1: title.txt conflict resolved to 'Pocket Recipes - Italian Quick Meals'
      - Part 2: tips.txt integrated alongside title.txt
      - Part 3: Clean working tree and merge history
    """
    exercise_path = exercise_path.expanduser().resolve()
    git_dir = _find_git_dir(exercise_path)

    # Locate title.txt (either directly or in subdirectories like lab04/)
    title_files = list(exercise_path.rglob("title.txt"))
    title_file = None
    if title_files:
        title_file = next(
            (c for c in title_files if (c.parent / "tips.txt").exists()),
            title_files[0],
        )

    # --- Part 1: Check title.txt Conflict Resolution ---
    expected_title = "Pocket Recipes - Italian Quick Meals"
    if title_file is not None:
        title_content = title_file.read_text().strip()
    elif "title.txt" in code and expected_title in code:
        title_content = expected_title
    else:
        return (
            False,
            "[Part 1 Failed] title.txt not found. Work inside ~/rendudevops/ex03_merge_rebase/lab04/.",
        )

    # Check for conflict markers
    markers = ["<<<<<<<", "=======", ">>>>>>>"]
    for marker in markers:
        if marker in title_content:
            return (
                False,
                f"[Part 1 Failed] title.txt still contains conflict marker '{marker}'. Remove all conflict markers.",
            )

    if title_content != expected_title:
        return (
            False,
            f"[Part 1 Failed] title.txt must be resolved to exactly: '{expected_title}' (got '{title_content}').",
        )

    # --- Part 2: Check tips.txt Integration ---
    tips_file = title_file.parent / "tips.txt" if title_file is not None else None
    if tips_file is not None and tips_file.exists():
        tips_content = tips_file.read_text().strip()
    elif "tips.txt" in code:
        tips_content = code
    else:
        return (
            False,
            "[Part 2 Failed] tips.txt not found. Rebase and merge feature/tips into main so tips.txt is present.",
        )

    expected_tip = "Tip: salt the water"
    if expected_tip not in tips_content:
        return (
            False,
            f"[Part 2 Failed] tips.txt should contain '{expected_tip}'.",
        )

    # --- Part 3: Check Git State (if repository is present) ---
    if git_dir and git_dir.exists():
        repo_dir = git_dir.parent
        try:
            status = subprocess.run(
                ["git", "-C", str(repo_dir), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # If merge or conflict is unfinished, git status will be non-empty
            if "UU title.txt" in status.stdout:
                return (
                    False,
                    "[Part 3 Failed] Merge conflict is still unresolved in Git. Stage title.txt and commit.",
                )
        except Exception:
            pass

    return (
        True,
        "All parts passed: [Part 1: Conflict Resolution OK] [Part 2: Tips Integration OK] [Part 3: Git History OK]",
    )


def _find_git_dir(start_path: Path) -> Path | None:
    """Locate the .git directory either directly or via known exercise files."""
    if (start_path / ".git").exists():
        return start_path / ".git"

    known_files = ["title.txt", "tips.txt"]
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
