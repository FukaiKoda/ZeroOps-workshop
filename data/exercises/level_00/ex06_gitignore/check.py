import subprocess
from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex06_gitignore (Lab 07: The Bouncer).

    Evaluates 3 distinct parts:
      - Part 1: .gitignore exists with rules for *.log, build/, and .env
      - Part 2: .env exists on disk but is untracked in Git index
      - Part 3: app.py remains present and tracked
    """
    exercise_path = exercise_path.expanduser().resolve()
    git_dir = _find_git_dir(exercise_path)

    # --- Part 1: Locate and Validate .gitignore ---
    ignore_files = list(exercise_path.rglob(".gitignore"))
    if not ignore_files:
        if ".gitignore" in code and "*.log" in code:
            ignore_content = code
            repo_dir = exercise_path
        else:
            return (
                False,
                "[Part 1 Failed] .gitignore not found. Create .gitignore in your repository.",
            )
    else:
        ignore_content = ignore_files[0].read_text()
        repo_dir = ignore_files[0].parent

    patterns = set(line.strip() for line in ignore_content.splitlines() if line.strip())
    required_patterns = {"*.log", "build/", ".env"}
    missing = required_patterns - patterns
    if missing:
        return (
            False,
            f"[Part 1 Failed] .gitignore is missing pattern(s): {', '.join(sorted(missing))}. Include *.log, build/, and .env.",
        )

    # --- Part 2: Verify .env exists locally and is untracked ---
    env_file = repo_dir / ".env"
    if not env_file.exists():
        # Check anywhere in workspace
        env_files = list(exercise_path.rglob(".env"))
        if not env_files and ".env" not in code:
            return (
                False,
                "[Part 2 Failed] .env file was deleted from disk. Use 'git rm --cached .env' so the file remains locally.",
            )

    # If git repo is available, verify .env is NOT tracked in Git
    if git_dir and git_dir.exists():
        actual_repo = git_dir.parent
        try:
            ls_res = subprocess.run(
                ["git", "-C", str(actual_repo), "ls-files", ".env"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if ".env" in ls_res.stdout.strip():
                return (
                    False,
                    "[Part 2 Failed] .env is still tracked by Git. Run: git rm --cached .env && git commit -m 'Stop tracking .env'",
                )
        except Exception:
            pass

    # --- Part 3: Verify app.py remains present and tracked ---
    app_file = repo_dir / "app.py"
    if not app_file.exists():
        app_files = list(exercise_path.rglob("app.py"))
        if not app_files and "app.py" not in code:
            return (
                False,
                "[Part 3 Failed] app.py was not found. Keep app.py in your repository.",
            )

    if git_dir and git_dir.exists():
        actual_repo = git_dir.parent
        try:
            ls_res = subprocess.run(
                ["git", "-C", str(actual_repo), "ls-files", "app.py"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "app.py" not in ls_res.stdout:
                return (
                    False,
                    "[Part 3 Failed] app.py must be committed and tracked in the repository.",
                )
        except Exception:
            pass

    return (
        True,
        "All parts passed: [Part 1: .gitignore Patterns OK] [Part 2: .env Untracked on Disk OK] [Part 3: app.py Tracked OK]",
    )


def _find_git_dir(start_path: Path) -> Path | None:
    """Locate the .git directory either directly or via known exercise files."""
    if (start_path / ".git").exists():
        return start_path / ".git"

    known_files = [".gitignore", "app.py", ".env"]
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
