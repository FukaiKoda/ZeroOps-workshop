from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import signal
import socket
import time
from pathlib import Path
from typing import Any, Callable, Dict, List


class TimeoutError(Exception):
    """Raised when a test case exceeds the configured timeout."""
    pass


@contextlib.contextmanager
def _timeout(seconds: int):
    """Context manager that raises TimeoutError after N seconds."""
    def handler(_signum, _frame):
        raise TimeoutError(f"Timeout after {seconds} seconds")

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@contextlib.contextmanager
def _block_network():
    """Best-effort network blockade during test execution."""
    original_socket = socket.socket
    original_create_connection = socket.create_connection

    def blocked(*_args, **_kwargs):
        raise RuntimeError("Network access is not allowed during tests")

    socket.socket = blocked  # type: ignore[assignment]
    socket.create_connection = blocked  # type: ignore[assignment]
    env_backup = {
        "HTTP_PROXY": os.environ.get("HTTP_PROXY"),
        "HTTPS_PROXY": os.environ.get("HTTPS_PROXY"),
        "ALL_PROXY": os.environ.get("ALL_PROXY"),
        "NO_PROXY": os.environ.get("NO_PROXY"),
    }
    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""
    os.environ["ALL_PROXY"] = ""
    os.environ["NO_PROXY"] = "*"
    try:
        yield
    finally:
        socket.socket = original_socket  # type: ignore[assignment]
        socket.create_connection = original_create_connection  # type: ignore[assignment]
        for key, value in env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _load_function(entrypoint: Path, function_name: str) -> Callable[..., Any]:
    """Dynamically import the entrypoint module and return the target function."""
    module_name = f"solution_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(module_name, entrypoint)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load solution module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    func = getattr(module, function_name, None)
    if func is None or not callable(func):
        raise RuntimeError(f"Function '{function_name}' not found")
    return func


def run_tests(testspec: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
    """Execute testspec cases against the user's solution and return results."""
    start = time.monotonic()
    entrypoint = workspace / testspec["entrypoint"]
    if not entrypoint.exists():
        return {
            "level": testspec["level"],
            "pass": False,
            "tests": [],
            "runtime_ms": 0,
            "error": f"Entrypoint not found: {entrypoint}",
        }

    try:
        func = _load_function(entrypoint, testspec["function"])
    except Exception as exc:
        return {
            "level": testspec["level"],
            "pass": False,
            "tests": [],
            "runtime_ms": 0,
            "error": str(exc),
        }

    timeout_seconds = int(testspec.get("constraints", {}).get("timeout_seconds", 2))
    results: List[Dict[str, Any]] = []
    all_passed = True

    for case in testspec["cases"]:
        name = case.get("name", "case")
        args = case.get("args", [])
        expected = case.get("expected")
        stdout = io.StringIO()
        stderr = io.StringIO()
        message = ""
        passed = True

        try:
            with _timeout(timeout_seconds), _block_network(), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                actual = func(*args)
            if actual != expected:
                passed = False
                message = f"Expected {expected} got {actual}"
        except TimeoutError as exc:
            passed = False
            message = str(exc)
        except Exception as exc:
            passed = False
            message = f"Exception: {exc}"

        if not passed:
            all_passed = False
        results.append({"name": name, "pass": passed, "message": message})

    runtime_ms = int((time.monotonic() - start) * 1000)
    return {
        "level": testspec["level"],
        "pass": all_passed,
        "tests": results,
        "runtime_ms": runtime_ms,
        "error": None,
    }
