import subprocess
from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex02_branching (Lab 03: Parallel Universes).

    Supports progressive grading with clear checkpoints:
      - Checkpoint A (Part 1 & 2): feature/dessert branch created with dessert.txt ('Tiramisu')
      - Checkpoint B (Part 3): main branch diverged with independent update ('Add basil' in pasta.txt)

    Returns targeted guidance telling the user what passed, what is missing,
    and the exact commands to continue or correct the exercise.
    """
    exercise_path = exercise_path.expanduser().resolve()
    git_dir = _find_git_dir(exercise_path)

    if git_dir and git_dir.exists():
        repo_dir = git_dir.parent
        return _grade_git(repo_dir, git_dir)

    # Fallback flat-file / server-side mode (when .git is omitted)
    return _grade_flat(code, exercise_path)


def _find_git_dir(start_path: Path) -> Path | None:
    """Locate the .git directory either in start_path, subdirs, or fallback rendu directory."""
    if (start_path / ".git").exists():
        return start_path / ".git"

    # Search in start_path
    known_files = ["dessert.txt", "pasta.txt", "salad.txt"]
    for known in known_files:
        found = list(start_path.rglob(known))
        if found:
            candidate = found[0].parent / ".git"
            if candidate.exists():
                return candidate

    # Search in parent dirs of start_path
    current = start_path
    while current.parent != current:
        if (current / ".git").exists():
            return current / ".git"
        current = current.parent

    # Fallback for server-side isolated temp workspace: look at student's local workspace if on same machine
    rendu_fallback = Path.home() / "rendudevops" / "ex02_branching"
    if rendu_fallback.exists():
        if (rendu_fallback / ".git").exists():
            return rendu_fallback / ".git"
        for known in known_files:
            found = list(rendu_fallback.rglob(known))
            if found:
                candidate = found[0].parent / ".git"
                if candidate.exists():
                    return candidate

    return None


def _grade_git(repo_dir: Path, git_dir: Path) -> Tuple[bool, str]:
    """Grade using Git commands in a live repository with progressive feedback."""
    # -------------------------------------------------------------
    # Step 1: Check branch feature/dessert existence
    # -------------------------------------------------------------
    has_branch = False
    try:
        # Check HEAD ref in case of newly switched unborn branch
        head_file = git_dir / "HEAD"
        head_content = head_file.read_text().strip() if head_file.exists() else ""
        if "feature/dessert" in head_content:
            has_branch = True

        if not has_branch:
            branches = list((git_dir / "refs" / "heads").rglob("*"))
            has_branch = any("feature/dessert" in b.as_posix() for b in branches)

        if not has_branch:
            res = subprocess.run(
                ["git", "-C", str(repo_dir), "branch", "--all"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            has_branch = "feature/dessert" in res.stdout
    except Exception:
        has_branch = False

    if not has_branch:
        return (
            False,
            "❌ [Part 1 Not Done] Branch 'feature/dessert' does not exist yet.\n\n"
            "👉 Next Step:\n"
            "Create and switch to the dessert branch:\n"
            "  git switch -c feature/dessert\n\n"
            "Then create 'dessert.txt' with 'Tiramisu', commit it, and submit to verify your progress!",
        )

    # -------------------------------------------------------------
    # Step 2: Check dessert.txt on feature/dessert
    # -------------------------------------------------------------
    has_dessert_file = False
    try:
        res_tree = subprocess.run(
            ["git", "-C", str(repo_dir), "ls-tree", "-r", "feature/dessert", "--name-only"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        has_dessert_file = "dessert.txt" in res_tree.stdout
    except Exception:
        has_dessert_file = False

    if not has_dessert_file:
        return (
            False,
            "✅ [Part 1: OK] Branch 'feature/dessert' exists!\n"
            "❌ [Part 2 Missing] 'dessert.txt' has not been committed on 'feature/dessert'.\n\n"
            "👉 How to complete Part 2:\n"
            "Make sure you are on 'feature/dessert', create the file, and commit it:\n"
            "  git switch feature/dessert\n"
            "  echo \"Tiramisu\" > dessert.txt\n"
            "  git add dessert.txt\n"
            "  git commit -m \"Add dessert\"\n\n"
            "Then submit again to verify your checkpoint!",
        )

    try:
        res_show = subprocess.run(
            ["git", "-C", str(repo_dir), "show", "feature/dessert:dessert.txt"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        dessert_content = res_show.stdout.strip()
    except Exception as e:
        return False, f"[Part 2 Failed] Could not read dessert.txt from branch: {e}"

    if dessert_content != "Tiramisu":
        return (
            False,
            "✅ [Part 1: OK] Branch 'feature/dessert' exists!\n"
            f"❌ [Part 2 Correction Needed] 'dessert.txt' must contain exactly 'Tiramisu' (found: '{dessert_content}').\n\n"
            "👉 How to correct:\n"
            "Update the recipe on 'feature/dessert' and commit:\n"
            "  git switch feature/dessert\n"
            "  echo \"Tiramisu\" > dessert.txt\n"
            "  git commit -am \"Fix dessert recipe\"\n\n"
            "Then submit again to verify!",
        )

    # -------------------------------------------------------------
    # Step 3: Check independent work on main (pasta with basil)
    # -------------------------------------------------------------
    has_basil = False
    try:
        res_pasta = subprocess.run(
            ["git", "-C", str(repo_dir), "show", "main:pasta.txt"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        has_basil = "Add basil" in res_pasta.stdout
    except Exception:
        pastas = list(repo_dir.rglob("pasta.txt"))
        if pastas and "Add basil" in pastas[0].read_text():
            has_basil = True

    if not has_basil:
        return (
            False,
            "✅ [Part 1: OK] Branch 'feature/dessert' created!\n"
            "✅ [Part 2: OK] 'dessert.txt' ('Tiramisu') committed on 'feature/dessert'!\n\n"
            "🎉 Checkpoint Passed! You have completed Parts 1 & 2.\n\n"
            "👉 Now Continue to Part 3 (Main Branch Divergence):\n"
            "1. Switch back to the 'main' branch:\n"
            "   git switch main\n"
            "2. Notice that 'dessert.txt' is not there (main remains untouched!).\n"
            "3. Append 'Add basil' to pasta.txt:\n"
            "   echo \"Add basil\" >> pasta.txt\n"
            "4. Commit the change on main:\n"
            "   git commit -am \"Add basil to pasta\"\n"
            "5. Run 'git lg' to see the two branches diverge.\n"
            "6. Submit again to complete the lab!",
        )

    return (
        True,
        "🎉 All parts completed successfully!\n"
        "✅ [Part 1: OK] Branch 'feature/dessert' created\n"
        "✅ [Part 2: OK] 'dessert.txt' ('Tiramisu') committed on feature branch\n"
        "✅ [Part 3: OK] Main branch independently updated with 'Add basil'\n\n"
        "Both branches now live in parallel without interfering with each other!",
    )


def _grade_flat(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """Grade server-side flat files (fallback when .git is not copied)."""
    desserts = list(exercise_path.rglob("dessert.txt"))
    dessert_content = ""
    if desserts:
        dessert_content = desserts[0].read_text().strip()
    elif "Tiramisu" in code:
        dessert_content = "Tiramisu"

    if not desserts and "dessert.txt" not in code:
        return (
            False,
            "❌ [Part 1/2 Not Done] 'dessert.txt' was not found.\n\n"
            "👉 Next Step:\n"
            "Create the 'feature/dessert' branch and commit 'dessert.txt' containing 'Tiramisu':\n"
            "  git switch -c feature/dessert\n"
            "  echo \"Tiramisu\" > dessert.txt\n"
            "  git add dessert.txt\n"
            "  git commit -m \"Add dessert\"\n\n"
            "Then submit to verify your checkpoint!",
        )

    if dessert_content != "Tiramisu":
        return (
            False,
            f"❌ [Part 2 Correction Needed] 'dessert.txt' must contain exactly 'Tiramisu' (found: '{dessert_content}').\n\n"
            "👉 How to correct:\n"
            "Update dessert.txt and commit:\n"
            "  echo \"Tiramisu\" > dessert.txt\n"
            "  git commit -am \"Fix dessert recipe\"",
        )

    pastas = list(exercise_path.rglob("pasta.txt"))
    pasta_content = pastas[0].read_text() if pastas else code
    if "Add basil" not in pasta_content:
        return (
            False,
            "✅ [Part 1: OK] Branch work detected!\n"
            "✅ [Part 2: OK] 'dessert.txt' with 'Tiramisu' is present!\n\n"
            "🎉 Checkpoint Passed! You have completed Parts 1 & 2.\n\n"
            "👉 Now Continue to Part 3 (Main Branch Divergence):\n"
            "1. Switch back to the 'main' branch:\n"
            "   git switch main\n"
            "2. Append 'Add basil' to pasta.txt:\n"
            "   echo \"Add basil\" >> pasta.txt\n"
            "3. Commit on main:\n"
            "   git commit -am \"Add basil to pasta\"\n"
            "4. Submit again to complete the lab!",
        )

    return (
        True,
        "🎉 All parts completed successfully!\n"
        "✅ [Part 1: OK] Branch 'feature/dessert' created\n"
        "✅ [Part 2: OK] 'dessert.txt' ('Tiramisu') committed on feature branch\n"
        "✅ [Part 3: OK] Main branch independently updated with 'Add basil'",
    )
