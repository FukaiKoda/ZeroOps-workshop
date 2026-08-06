"""Validator for Level 00 Exercise 07 — Marketplace Actions."""

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


def _validate_workflow(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []

    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append("Missing 'jobs:' section.")
        return False, errors

    found_setup_python = False
    found_python_version_311 = False

    all_steps: List[Dict[str, Any]] = []
    for job_name, job_config in jobs.items():
        if isinstance(job_config, dict):
            steps = job_config.get("steps", [])
            if isinstance(steps, list):
                all_steps.extend([s for s in steps if isinstance(s, dict)])

    for step in all_steps:
        uses = str(step.get("uses", "")).lower()
        if "actions/setup-python" in uses:
            if "@v5" in uses or "v5." in uses:
                found_setup_python = True
            else:
                errors.append(f"Action version pinning check failed: expected 'actions/setup-python@v5', got '{uses}'.")

            with_block = step.get("with")
            if isinstance(with_block, dict):
                py_ver = str(with_block.get("python-version", "")).strip("'\" ")
                if py_ver == "3.11":
                    found_python_version_311 = True
                else:
                    errors.append(f"Expected python-version: '3.11' inside with: block, got '{py_ver}'.")
            else:
                errors.append("Missing 'with:' block under 'actions/setup-python@v5'.")

    if not found_setup_python:
        if not any("actions/setup-python" in str(s.get("uses", "")).lower() for s in all_steps):
            errors.append("Missing step using 'actions/setup-python@v5'.")

    if not found_python_version_311:
        if not any("3.11" in str(s.get("with", {})) for s in all_steps):
            errors.append("Missing configuration 'python-version: '3.11'' inside 'with:' block.")

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    files = _find_workflow_files(cwd)
    contents = []

    if files:
        for f in files:
            try:
                contents.append((f.name, f.read_text()))
            except Exception as e:
                return False, f"Could not read workflow file '{f.name}': {e}"
    elif code.strip():
        contents.append(("workflow.yml", code))
    else:
        return False, "No workflow file found in 'ex07_marketplace_actions/'."

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
            all_errors.append(f"[{filename}]:\n  ❌ " + "\n  ❌ ".join(step_errors))

    if valid_count > 0:
        return (
            True,
            "✅ Excellent work! Your workflow properly uses and pins Marketplace action 'actions/setup-python@v5'.\n"
            "Checks passed:\n"
            "  ✓ Uses pinned action 'actions/setup-python@v5'\n"
            "  ✓ Configured with python-version: '3.11'\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
