from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grader for ex01_config (Lab 02: Introduce Yourself).

    Evaluates 3 distinct parts:
      - Part 1: config-report.txt exists in the exercise workspace
      - Part 2: Git identity (user.name and user.email) documented
      - Part 3: Git aliases (alias.st and alias.lg) documented
    """
    exercise_path = exercise_path.expanduser().resolve()

    # --- Part 1: Locate config-report.txt ---
    reports = list(exercise_path.rglob("config-report.txt"))
    if not reports:
        if "config-report.txt" in code:
            report_content = code
        else:
            return (
                False,
                "[Part 1 Failed] config-report.txt not found. Save your Git configuration report in config-report.txt.",
            )
    else:
        report_content = reports[0].read_text()

    # Normalize content lines
    lines = [line.strip() for line in report_content.splitlines() if line.strip()]
    if not lines:
        return (
            False,
            "[Part 1 Failed] config-report.txt is empty. Write your configuration details to this file.",
        )

    # --- Part 2: Validate Identity (user.name and user.email) ---
    has_user_name = "user.name" in report_content or any(
        len(l) > 1 and "@" not in l and "status" not in l and "log" not in l
        for l in lines
    )
    has_user_email = "user.email" in report_content or any("@" in l for l in lines)

    if not has_user_name:
        return (
            False,
            "[Part 2 Failed] config-report.txt is missing user.name. Include your Git username.",
        )
    if not has_user_email:
        return (
            False,
            "[Part 2 Failed] config-report.txt is missing user.email. Include your Git email (e.g. user.email=you@example.com).",
        )

    # --- Part 3: Validate Aliases (st and lg) ---
    has_alias_st = "alias.st" in report_content or any("status" in l for l in lines)
    has_alias_lg = "alias.lg" in report_content or any("log" in l for l in lines)

    if not has_alias_st:
        return (
            False,
            "[Part 3 Failed] config-report.txt is missing alias.st. Document your status alias (e.g. alias.st=status -sb).",
        )
    if not has_alias_lg:
        return (
            False,
            "[Part 3 Failed] config-report.txt is missing alias.lg. Document your log alias (e.g. alias.lg=log --oneline --graph --all --decorate).",
        )

    return (
        True,
        "All parts passed: [Part 1: Report File OK] [Part 2: Git Identity OK] [Part 3: Git Aliases OK]",
    )
