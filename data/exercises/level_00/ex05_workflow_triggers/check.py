"""Validator for Level 00 Exercise 05 — Workflow Triggers."""

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

    # Handle PyYAML parsing 'on' as boolean True
    trigger = data.get("on") or data.get(True) or data.get("true")
    if trigger is None:
        errors.append("Missing trigger section 'on:'.")
        return False, errors

    found_pr = False
    found_push_main = False

    raw_yaml_lower = raw_yaml.lower()

    if isinstance(trigger, str):
        if trigger == "pull_request":
            found_pr = True
        if trigger == "push":
            errors.append("Push trigger must be filtered to branch 'main' (e.g., push: branches: [main]).")
    elif isinstance(trigger, list):
        trigger_strs = [str(t).lower() for t in trigger]
        if "pull_request" in trigger_strs:
            found_pr = True
    elif isinstance(trigger, dict):
        if "pull_request" in trigger or True in trigger:  # PyYAML might map bare pull_request
            found_pr = True
        # Check pull_request in raw yaml as fallback
        if "pull_request" in raw_yaml_lower:
            found_pr = True

        push_config = trigger.get("push")
        if push_config is not None:
            if isinstance(push_config, dict):
                branches = push_config.get("branches")
                if branches:
                    branch_list = [branches] if isinstance(branches, str) else branches
                    if isinstance(branch_list, list) and any("main" in str(b).lower() for b in branch_list):
                        found_push_main = True
            elif push_config is None:  # bare push:
                pass

    if "pull_request" in raw_yaml_lower:
        found_pr = True

    if "branches" in raw_yaml_lower and "main" in raw_yaml_lower:
        found_push_main = True

    if not found_pr:
        errors.append("Missing 'pull_request' trigger event.")

    if not found_push_main:
        errors.append("Missing 'push' trigger filtered by 'branches: [main]'.")

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
        return False, "No workflow file found in 'ex05_workflow_triggers/'."

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
            "✅ Perfect! Your workflow triggers are properly configured for pull_request and push to main.\n"
            "Checks passed:\n"
            "  ✓ Triggers on 'pull_request'\n"
            "  ✓ Triggers on 'push' targeting branch 'main'\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
