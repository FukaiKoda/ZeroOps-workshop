from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

SESSION = requests.Session()

try:
    from client.auth import build_identity, signed_headers
    from client.models import Meta
    from client.runner import run_tests
except ImportError:  # pragma: no cover
    from auth import build_identity, signed_headers
    from models import Meta
    from runner import run_tests



def _server_url(args: argparse.Namespace) -> str:
    """Resolve server URL from CLI args or environment."""
    return args.server or os.getenv("SERVER_URL", "").rstrip("/")


def _workspace_base(args: argparse.Namespace) -> Path:
    """Resolve the workspace base directory."""
    return Path(args.workspace or Path.home()).expanduser()


def _zeroops_dir(base: Path) -> Path:
    """Return the zeroops root directory under the workspace."""
    return base / "zeroops"


def _subjects_dir(base: Path) -> Path:
    """Return the subjects directory under the zeroops workspace."""
    return _zeroops_dir(base) / "subjects"


def _rendu_dir(base: Path) -> Path:
    """Return the rendu directory under the zeroops workspace."""
    return _zeroops_dir(base) / "rendu"


def _level_name(level: int) -> str:
    """Format a numeric level as a zero-padded folder name."""
    return f"level{level:02d}"


def _level_dir(base: Path, level: int) -> Path:
    """Return the path to the level directory under subjects/."""
    return _subjects_dir(base) / _level_name(level)


def _meta_path(level_dir: Path) -> Path:
    """Return the path to the meta file inside a level directory."""
    return level_dir / ".meta.json"


def _request_json(method: str, url: str, body: Dict[str, Any], params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Send a signed JSON request and return the JSON response."""
    headers = signed_headers(body)
    headers.setdefault("Connection", "keep-alive")
    resp = SESSION.request(method, url, json=body, headers=headers, params=params, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"{resp.status_code}: {resp.text}")
    return resp.json()


def _ensure_structure(base: Path, total_levels: int) -> None:
    """Create the zeroops workspace folder structure."""
    _zeroops_dir(base).mkdir(parents=True, exist_ok=True)
    _subjects_dir(base).mkdir(parents=True, exist_ok=True)
    _rendu_dir(base).mkdir(parents=True, exist_ok=True)
    for level in range(1, total_levels + 1):
        _level_dir(base, level).mkdir(parents=True, exist_ok=True)


def _clean_level_dir(level_dir: Path) -> None:
    """Remove all files and subdirectories inside a level directory."""
    if not level_dir.exists():
        return
    for path in level_dir.iterdir():
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    try:
                        child.rmdir()
                    except OSError:
                        pass
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_dir():
                    try:
                        child.rmdir()
                    except OSError:
                        pass
            try:
                path.rmdir()
            except OSError:
                pass
        else:
            path.unlink()


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync identity and fetch the subject for the current level."""
    server_url = _server_url(args)
    if not server_url:
        raise RuntimeError("SERVER_URL is required")
    identity = build_identity()

    sync_data = _request_json("POST", f"{server_url}/v1/sync", identity)
    level = int(sync_data["level"])
    total_levels = int(sync_data.get("total_levels", level))

    subject_data = _request_json(
        "GET",
        f"{server_url}/v1/subject",
        identity,
        params={"username": identity["username"]},
    )

    level = int(subject_data["level"])
    total_levels = int(subject_data.get("total_levels", total_levels))
    base = _workspace_base(args)
    _ensure_structure(base, total_levels)
    level_dir = _level_dir(base, level)

    _clean_level_dir(level_dir)
    (level_dir / "subject.en.txt").write_text(subject_data["subject"], encoding="utf-8")

    meta = Meta(server_url=server_url, username=identity["username"], level=level, last_sync=identity["timestamp"])
    meta.save(_meta_path(level_dir))
    print(f"Synced level {level} to {level_dir}")


def cmd_subject(args: argparse.Namespace) -> None:
    """Fetch only the subject text for the current level."""
    server_url = _server_url(args)
    if not server_url:
        raise RuntimeError("SERVER_URL is required")
    identity = build_identity()

    data = _request_json(
        "GET",
        f"{server_url}/v1/subject",
        identity,
        params={"username": identity["username"]},
    )
    level = int(data["level"])
    total_levels = int(data.get("total_levels", level))
    base = _workspace_base(args)
    _ensure_structure(base, total_levels)
    level_dir = _level_dir(base, level)
    _clean_level_dir(level_dir)
    (level_dir / "subject.en.txt").write_text(data["subject"], encoding="utf-8")
    print(f"Updated subject for level {level}")


def cmd_correct(args: argparse.Namespace) -> None:
    """Fetch testspec, run local tests, and submit results."""
    server_url = _server_url(args)
    if not server_url:
        raise RuntimeError("SERVER_URL is required")
    identity = build_identity()

    spec_data = _request_json(
        "GET",
        f"{server_url}/v1/testspec",
        identity,
        params={"username": identity["username"]},
    )
    testspec = spec_data["testspec"]
    level = int(spec_data["level"])

    base = _workspace_base(args)
    _ensure_structure(base, level)
    level_dir = _level_dir(base, level)
    results = run_tests(testspec, level_dir)

    submit_body = {"identity": identity, "results": results}
    response = _request_json("POST", f"{server_url}/v1/submit", submit_body)

    meta_path = _meta_path(level_dir)
    meta = Meta.load(meta_path) or Meta(server_url=server_url, username=identity["username"], level=level, last_sync=identity["timestamp"])
    meta.level = int(response["level"])
    meta.last_sync = identity["timestamp"]
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta_payload.update({
        "server_url": meta.server_url,
        "username": meta.username,
        "level": meta.level,
        "last_sync": meta.last_sync,
        "last_attempt_summary": response.get("feedback", ""),
    })
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    print(response["feedback"])
    print(f"Current level: {response['level']}")


def cmd_status(args: argparse.Namespace) -> None:
    """Show server level and local metadata summary."""
    server_url = _server_url(args)
    if not server_url:
        raise RuntimeError("SERVER_URL is required")
    identity = build_identity()

    sync_data = _request_json("POST", f"{server_url}/v1/sync", identity)
    server_level = int(sync_data["level"])

    base = _workspace_base(args)
    level_dir = _level_dir(base, server_level)
    meta = Meta.load(_meta_path(level_dir))

    print(f"Server level: {server_level}")
    if meta:
        print(f"Local meta: level={meta.level}, last_sync={meta.last_sync}")
        meta_path = _meta_path(level_dir)
        payload = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        summary = payload.get("last_attempt_summary", "")
        if summary:
            print(f"Last attempt: {summary}")
    else:
        print("Local meta: not found")


def main() -> None:
    """CLI entrypoint for the exercise client."""
    parser = argparse.ArgumentParser(description="Exercise platform client")
    parser.add_argument("--server", help="Server URL")
    parser.add_argument("--workspace", help="Workspace base path")
    parser.add_argument("--force", action="store_true", help="Overwrite starter files")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("sync")
    sub.add_parser("subject")
    sub.add_parser("correct")
    sub.add_parser("grademe")
    sub.add_parser("status")
    sub.add_parser("tui")

    args = parser.parse_args()
    if args.command in (None, "tui"):
        try:
            from client.tui import run_tui
        except ImportError:  # pragma: no cover
            from tui import run_tui
        run_tui(args.server or os.getenv("SERVER_URL", ""), args.workspace, args.force)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "subject":
        cmd_subject(args)
    elif args.command in ("correct", "grademe"):
        cmd_correct(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
