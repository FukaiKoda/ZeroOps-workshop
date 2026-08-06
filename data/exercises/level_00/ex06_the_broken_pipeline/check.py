"""Validator for Level 00 Exercise 06 — The Broken Pipeline."""

import yaml
from pathlib import Path
from typing import Tuple, List, Dict, Any


def _find_workflow_files(cwd: Path) -> List[Path]:
    files: List[Path] = []
    search_dirs = [cwd, cwd / ".github" / "workflows", cwd / "workflows"]
    for d in search_dirs:
        if d.exists() and d.is_dir():
            for ext in ["*.yml", "*.yaml"]:
                files.extend(d.glob(ext))
    seen = set()
    unique_files = []
    for f in files:
        if f.resolve() not in seen:
            seen.add(f.resolve())
            unique_files.append(f)
    return sorted(unique_files)


def _parse_yaml(content: str) -> Tuple[bool, Any, str]:
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False, None, "YAML root must be a dictionary."
        return True, data, ""
    except yaml.YAMLError as e:
        return False, None, f"YAML Syntax Error: {e}"


def _validate_single_fixed_file(filename: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []

    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append(f"[{filename}] Missing valid 'jobs:' section.")
        return False, errors

    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            errors.append(f"[{filename}] Job '{job_name}' must be a dictionary.")
            continue

        if "runs-on" not in job_config:
            errors.append(f"[{filename}] Job '{job_name}' is missing 'runs-on:'. Check indentation!")

        if "steps" not in job_config:
            if "step" in job_config:
                errors.append(f"[{filename}] Invalid key 'step:' found in job '{job_name}'. Use plural 'steps:'.")
            else:
                errors.append(f"[{filename}] Job '{job_name}' is missing 'steps:' list.")
        else:
            steps = job_config.get("steps")
            if not isinstance(steps, list) or len(steps) == 0:
                errors.append(f"[{filename}] Job '{job_name}' steps must be a non-empty list.")

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    files = _find_workflow_files(cwd)

    if not files:
        return False, (
            "No workflow files found in 'ex06_the_broken_pipeline/'!\n"
            "Please create and fix the three files: 06a_colons.yml, 06b_indentation.yml, 06c_key_name.yml."
        )

    all_errors = []
    valid_files = set()

    for f in files:
        try:
            content = f.read_text()
        except Exception as e:
            all_errors.append(f"[{f.name}] Could not read file: {e}")
            continue

        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{f.name}] {err_str}")
            continue

        valid, step_errors = _validate_single_fixed_file(f.name, data)
        if valid:
            valid_files.add(f.name.lower())
        else:
            all_errors.extend(step_errors)

    if len(valid_files) < 3 and len(files) < 3:
        return False, (
            f"Found only {len(files)} file(s). You must fix all 3 broken pipeline files:\n"
            "  - 06a_colons.yml\n  - 06b_indentation.yml\n  - 06c_key_name.yml\n\n"
            + ("Errors:\n" + "\n".join(all_errors) if all_errors else "")
        )

    if len(all_errors) == 0 and len(valid_files) >= 3:
        return (
            True,
            "✅ Excellent debugging! All three broken YAML workflows have been successfully fixed:\n"
            "  ✓ 06a_colons.yml: Fixed missing key/value colons\n"
            "  ✓ 06b_indentation.yml: Fixed runs-on indentation\n"
            "  ✓ 06c_key_name.yml: Fixed step -> steps key name\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
