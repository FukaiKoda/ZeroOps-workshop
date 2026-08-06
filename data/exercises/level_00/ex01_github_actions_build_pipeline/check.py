"""Validator for Level 02 Exercise 00 — GitHub Actions Build Pipeline."""

import yaml
from pathlib import Path
from typing import Tuple, List, Dict, Any


def _find_workflow_files(cwd: Path) -> List[Path]:
    """Find workflow files inside the isolated exercise folder."""
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
            return False, None, "YAML root must be a dictionary (key-value mapping)."
        return True, data, ""
    except yaml.YAMLError as e:
        return False, None, f"YAML Syntax Error: {e}"


def _validate_workflow(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []

    # 1. Trigger check ('on' or 'on:' key)
    if "on" not in data and True not in data:  # 'on' can parse as boolean True in PyYAML
        # Check if PyYAML converted 'on' to True
        if True not in data and "on" not in data and "True" not in data:
            errors.append("Missing trigger event 'on:' (e.g. on: push or on: [push]).")

    # 2. Jobs check
    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append("Missing 'jobs:' configuration mapping.")
        return False, errors

    # Search across all jobs for required steps
    found_checkout = False
    found_python = False
    found_pwd = False
    found_ls = False

    all_steps: List[Dict[str, Any]] = []

    for job_name, job_config in jobs.items():
        if isinstance(job_config, dict):
            steps = job_config.get("steps", [])
            if isinstance(steps, list):
                all_steps.extend([s for s in steps if isinstance(s, dict)])

    if not all_steps:
        errors.append("No 'steps:' found in any job configuration.")
        return False, errors

    for step in all_steps:
        # Check 'uses' for actions/checkout
        uses_val = str(step.get("uses", "")).lower()
        if "actions/checkout" in uses_val:
            found_checkout = True

        # Check 'run' commands
        run_val = str(step.get("run", "")).lower()

        if "python" in run_val:
            found_python = True

        if "pwd" in run_val:
            found_pwd = True

        # Matches 'ls', 'ls -l', 'ls -la', 'dir'
        if any(cmd in run_val for cmd in ["ls", "dir"]):
            found_ls = True

    if not found_checkout:
        errors.append("Missing checkout step using 'actions/checkout' (e.g., uses: actions/checkout@v4).")

    if not found_python:
        errors.append("Missing step to print Python version (e.g., run: python --version or run: python3 --version).")

    if not found_pwd:
        errors.append("Missing step to print current directory (e.g., run: pwd).")

    if not found_ls:
        errors.append("Missing step to list repository files (e.g., run: ls -la or run: ls).")

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    # 1. Search for workflow files in local workspace
    files = _find_workflow_files(cwd)
    contents = []

    if files:
        for f in files:
            try:
                contents.append((f.name, f.read_text()))
            except Exception as e:
                return False, f"Could not read workflow file {f.name}: {e}"
    elif code.strip():
        # Fallback: test code string provided directly
        contents.append(("workflow.yml", code))
    else:
        return False, (
            "No workflow file found!\n"
            "Please create a GitHub Actions workflow file in your repository at:\n"
            "  .github/workflows/build.yml"
        )

    all_errors = []
    valid_count = 0

    for filename, content in contents:
        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{filename}] {err_str}")
            continue

        valid, step_errors = _validate_workflow(data)
        if valid:
            valid_count += 1
        else:
            all_errors.append(f"[{filename}]:\n  - " + "\n  - ".join(step_errors))

    if valid_count > 0:
        return (
            True,
            "✅ Excellent work! Your GitHub Actions build pipeline workflow is properly structured and meets all requirements.\n"
            "- Uses actions/checkout\n"
            "- Prints Python version\n"
            "- Prints current directory (pwd)\n"
            "- Lists repository files (ls)"
        )

    return (
        False,
        "Validation failed:\n" + "\n".join(all_errors)
    )
