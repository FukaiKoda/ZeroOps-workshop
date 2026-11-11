from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex00_basic_workflow (Lab 01: The Careful Commit).

    Evaluates 3 distinct parts:
      - Part 1: Initial pasta recipe in pasta.txt
      - Part 2: Serving tip appended in pasta.txt
      - Part 3: Secondary recipe in salad.txt alongside pasta.txt
    """
    exercise_path = exercise_path.expanduser().resolve()

    # Locate pasta.txt (may be at root or inside pocket-recipes/)
    pasta_files = list(exercise_path.rglob("pasta.txt"))
    pasta = None
    if pasta_files:
        # Prefer the candidate with a sibling salad.txt
        pasta = next(
            (c for c in pasta_files if (c.parent / "salad.txt").exists()),
            pasta_files[0],
        )

    # --- Part 1 Check: Initial Recipe ---
    required_recipe = "Pasta: boil water, add pasta, cook 10 minutes"
    if pasta is not None:
        content_pasta = pasta.read_text()
        if required_recipe not in content_pasta:
            return False, f"[Part 1 Failed] pasta.txt is missing initial recipe line: '{required_recipe}'"
    elif "pasta.txt" in code and required_recipe in code:
        content_pasta = code
    else:
        return (
            False,
            "[Part 1 Failed] pasta.txt not found. Create pocket-recipes/pasta.txt with the recipe.",
        )

    # --- Part 2 Check: Serving Tip ---
    required_tip = "Serve hot"
    if required_tip not in content_pasta:
        return (
            False,
            f"[Part 2 Failed] pasta.txt is missing serving tip: '{required_tip}'. Append it to pasta.txt.",
        )

    # --- Part 3 Check: Salad Recipe ---
    salad = pasta.parent / "salad.txt" if pasta is not None else None
    if salad is not None and salad.exists():
        content_salad = salad.read_text()
    elif "salad.txt" in code:
        content_salad = code
    else:
        return (
            False,
            "[Part 3 Failed] salad.txt was not found. Keep salad.txt in the repository alongside pasta.txt.",
        )

    required_salad = "Salad: chop vegetables, add oil"
    if required_salad not in content_salad:
        return (
            False,
            f"[Part 3 Failed] salad.txt should contain: '{required_salad}'",
        )

    return (
        True,
        "All parts passed: [Part 1: Initial Recipe OK] [Part 2: Serving Tip OK] [Part 3: Salad Recipe OK]",
    )
