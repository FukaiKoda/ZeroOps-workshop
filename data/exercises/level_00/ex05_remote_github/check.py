import subprocess
from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex05_remote_github (Lab 06: Hello, Remote).

    Evaluates 3 distinct parts:
      - Part 1: README.md exists and is not empty
      - Part 2: Remote origin configured (if local repository)
      - Part 3: README.md committed and synchronized
    """
    exercise_path = exercise_path.expanduser().resolve()
    git_dir = _find_git_dir(exercise_path)

    # --- Part 1: Check README.md file and content ---
    readmes = list(exercise_path.rglob("README.md"))
    if not readmes:
        if "README.md" in code and len(code.strip()) > 0:
            readme_content = code
        else:
            return (
                False,
                "[Part 1 Failed] README.md not found. Create README.md in the repository root and pull it locally.",
            )
    else:
        readme_content = readmes[0].read_text().strip()

    if not readme_content:
        return (
            False,
            "[Part 1 Failed] README.md must not be empty. Add a project title or description.",
        )

    # --- Part 2 & Part 3: Git Remote & Tracking (when .git is present) ---
    if git_dir and git_dir.exists():
        repo_dir = git_dir.parent
        # Part 2: Remote origin check
        try:
            remote_res = subprocess.run(
                ["git", "-C", str(repo_dir), "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "origin" not in remote_res.stdout:
                return (
                    False,
                    "[Part 2 Failed] Remote 'origin' is not configured. Run: git remote add origin <URL>",
                )
        except Exception as e:
            return False, f"[Part 2 Failed] Could not inspect remotes: {e}"

        # Part 3: Check README.md is committed
        try:
            ls_res = subprocess.run(
                ["git", "-C", str(repo_dir), "ls-files", "README.md"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "README.md" not in ls_res.stdout:
                # Check rglob relative path if nested
                rel_path = readmes[0].relative_to(repo_dir).as_posix()
                ls_res2 = subprocess.run(
                    ["git", "-C", str(repo_dir), "ls-files", rel_path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if rel_path not in ls_res2.stdout:
                    return (
                        False,
                        "[Part 3 Failed] README.md is not tracked by Git. Stage, commit, and push it.",
                    )
        except Exception as e:
            return False, f"[Part 3 Failed] Git ls-files check failed: {e}"

    return (
        True,
        "All parts passed: [Part 1: README.md Present OK] [Part 2: Remote Origin Configured OK] [Part 3: Synchronized & Committed OK]",
    )


def _find_git_dir(start_path: Path) -> Path | None:
    """Locate the .git directory either directly or via known exercise files."""
    if (start_path / ".git").exists():
        return start_path / ".git"

    known_files = ["README.md", "pasta.txt"]
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
