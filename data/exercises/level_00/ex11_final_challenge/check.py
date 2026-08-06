"""Validator for Level 00 Exercise 11 — Final Challenge."""

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


def _validate_workflow(data: Dict[str, Any], raw_yaml: str) -> Tuple[bool, List[str]]:
    errors = []
    raw_lower = raw_yaml.lower()

    # 1. Triggers check
    if "pull_request" not in raw_lower:
        errors.append("Missing trigger 'pull_request'.")
    if "main" not in raw_lower or "branches" not in raw_lower:
        errors.append("Missing trigger 'push' filtered by branch 'main'.")

    # 2. Env check
    top_env = data.get("env") or {}
    jobs = data.get("jobs", {})
    all_env_keys = set(top_env.keys() if isinstance(top_env, dict) else [])
    if isinstance(jobs, dict):
        for j in jobs.values():
            if isinstance(j, dict) and "env" in j and isinstance(j["env"], dict):
                all_env_keys.update(j["env"].keys())

    if "PROJECT_NAME" not in all_env_keys:
        errors.append("Missing environment variable 'PROJECT_NAME' in env: block.")

    # 3. Steps checks
    all_steps: List[Dict[str, Any]] = []
    if isinstance(jobs, dict):
        for j in jobs.values():
            if isinstance(j, dict):
                steps = j.get("steps", [])
                if isinstance(steps, list):
                    all_steps.extend([s for s in steps if isinstance(s, dict)])

    found_checkout = False
    found_setup_python = False
    found_pip = False
    found_pytest = False
    found_success_msg = False

    for step in all_steps:
        uses = str(step.get("uses", "")).lower()
        run_cmd = str(step.get("run", "")).lower()

        if "actions/checkout" in uses:
            found_checkout = True

        if "actions/setup-python" in uses:
            if "@v5" in uses or "v5." in uses:
                found_setup_python = True

        if "pip" in run_cmd:
            found_pip = True

        if "pytest" in run_cmd:
            found_pytest = True

        if "echo" in run_cmd and ("success" in run_cmd or "complete" in run_cmd or "passed" in run_cmd or "done" in run_cmd or "🎉" in run_cmd):
            found_success_msg = True

    if not found_checkout:
        errors.append("Missing checkout step using 'actions/checkout@v4'.")

    if not found_setup_python:
        errors.append("Missing pinned Python setup step using 'actions/setup-python@v5'.")

    if not found_pip:
        errors.append("Missing dependency installation step (e.g. run: pip install pytest or pip install -r requirements.txt).")

    if not found_pytest:
        errors.append("Missing test execution step (e.g. run: pytest).")

    if not found_success_msg:
        errors.append("Missing final pipeline success message step (e.g. run: echo 'Pipeline succeeded!').")

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
        return False, "No workflow file found in 'ex11_final_challenge/'."

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
            "🏆 CONGRATULATIONS! You have completed the Final Challenge and built a production-grade CI pipeline!\n"
            "Checks passed:\n"
            "  ✓ Pull request & main push branch triggers\n"
            "  ✓ Checkout & pinned actions/setup-python@v5\n"
            "  ✓ PROJECT_NAME environment variable configuration\n"
            "  ✓ Dependency installation & Pytest execution\n"
            "  ✓ Final pipeline success notification\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
