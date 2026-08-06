"""Validator for Level 00 Exercise 08 — CI Detective."""

import json
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any


CORRECT_ANSWERS = {
    "scenario_a": 2,  # setup-python missing
    "scenario_b": 3,  # checkout missing
    "scenario_c": 1,  # wrong working directory / repo structure mismatch
}


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    answers_file = cwd / "answers.json"
    if not answers_file.exists():
        answers_file = cwd / "answers.yml"

    if not answers_file.exists():
        return False, (
            "File 'answers.json' not found in 'ex08_ci_detective/'!\n"
            "Please create 'answers.json' with your scenario choices:\n"
            '{\n  "scenario_a": 2,\n  "scenario_b": 3,\n  "scenario_c": 1\n}'
        )

    try:
        content = answers_file.read_text()
        if answers_file.name.endswith(".json"):
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
    except Exception as e:
        return False, f"Could not parse '{answers_file.name}': {e}"

    if not isinstance(data, dict):
        return False, "Root of 'answers.json' must be a JSON object mapping scenario keys to option numbers."

    errors = []
    for scenario, correct_opt in CORRECT_ANSWERS.items():
        user_val = data.get(scenario)
        if user_val is None:
            errors.append(f"Missing answer for '{scenario}'.")
        else:
            try:
                user_val_int = int(user_val)
                if user_val_int != correct_opt:
                    errors.append(f"Scenario '{scenario}' choice {user_val_int} is incorrect.")
            except ValueError:
                errors.append(f"Scenario '{scenario}' answer must be an integer option number.")

    if not errors:
        return (
            True,
            "✅ Excellent diagnostic work, CI Detective!\n"
            "All three build failure log scenarios correctly diagnosed:\n"
            "  ✓ Scenario A: Identified missing setup-python\n"
            "  ✓ Scenario B: Identified missing checkout\n"
            "  ✓ Scenario C: Identified working directory mismatch\n"
        )

    return False, "Validation failed:\n  ❌ " + "\n  ❌ ".join(errors)
