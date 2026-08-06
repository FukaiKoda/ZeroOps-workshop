"""Validator for Level 00 Exercise 02 — GitHub Context Variables."""

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


def _validate_workflow(data: Dict[str, Any], raw_yaml: str) -> Tuple[bool, List[str]]:
    errors = []

    # 1. Trigger check ('on' key)
    if "on" not in data and True not in data and "True" not in data:
        errors.append("Missing trigger event 'on:' (e.g. on: push).")

    # 2. Jobs check
    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append("Missing 'jobs:' section.")
        return False, errors

    found_checkout = False
    found_repo_context = False
    found_branch_context = False
    found_sha_context = False

    all_steps: List[Dict[str, Any]] = []
    for job_name, job_config in jobs.items():
        if isinstance(job_config, dict):
            steps = job_config.get("steps", [])
            if isinstance(steps, list):
                all_steps.extend([s for s in steps if isinstance(s, dict)])

    if not all_steps:
        errors.append("No 'steps:' defined in any job configuration.")
        return False, errors

    for step in all_steps:
        uses_val = str(step.get("uses", "")).lower()
        run_val = str(step.get("run", "")).lower()

        if "actions/checkout" in uses_val:
            found_checkout = True

        if "github.repository" in run_val:
            found_repo_context = True

        if "github.ref_name" in run_val or "github.ref" in run_val:
            found_branch_context = True

        if "github.sha" in run_val:
            found_sha_context = True

    # Secondary check in raw YAML text to handle PyYAML string edge-cases
    raw_yaml_lower = raw_yaml.lower()
    if "github.repository" in raw_yaml_lower:
        found_repo_context = True
    if "github.ref_name" in raw_yaml_lower or "github.ref" in raw_yaml_lower:
        found_branch_context = True
    if "github.sha" in raw_yaml_lower:
        found_sha_context = True

    if not found_checkout:
        errors.append("Missing checkout step using 'actions/checkout' (e.g. uses: actions/checkout@v4).")

    if not found_repo_context:
        errors.append("Missing explicit GitHub context expression '${{ github.repository }}'.")

    if not found_branch_context:
        errors.append("Missing explicit GitHub context expression '${{ github.ref_name }}' or '${{ github.ref }}'.")

    if not found_sha_context:
        errors.append("Missing explicit GitHub context expression '${{ github.sha }}'.")

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    """Standard ZeroOps Grader Contract."""
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
        return False, (
            "No workflow file found!\n"
            "Please create your workflow file inside directory 'ex02_multi_step_workflow/'."
        )

    all_errors = []
    valid_count = 0

    for filename, content in contents:
        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{filename}] {err_str}")
            continue

        valid, step_errors = _validate_workflow(data, content)
        if valid:
            valid_count += 1
        else:
            all_errors.append(f"[{filename}]:\n  ❌ " + "\n  ❌ ".join(step_errors))

    if valid_count > 0:
        return (
            True,
            "✅ Excellent work! Your workflow correctly uses GitHub context expressions.\n"
            "Checks passed:\n"
            "  ✓ Uses actions/checkout\n"
            "  ✓ Uses ${{ github.repository }} context expression\n"
            "  ✓ Uses ${{ github.ref_name }} context expression\n"
            "  ✓ Uses ${{ github.sha }} context expression\n"
        )

    return (
        False,
        "Validation failed:\n" + "\n".join(all_errors)
    )
