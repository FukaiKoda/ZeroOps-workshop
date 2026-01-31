from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, status

BASE_DIR = Path(__file__).resolve().parent

from shared.schema import (
    AdminUser,
    AdminUsersResponse,
    Identity,
    StarterFile,
    SubjectResponse,
    SubmitRequest,
    SubmitResponse,
    SyncResponse,
    TestSpec,
    TestSpecResponse,
)
from shared.util import now_iso

from server.auth import verify_request_signature
from server.db import JsonDB

app = FastAPI(title="Exercise Platform")

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db.json"))
LEVELS_DIR = BASE_DIR / "levels"

db = JsonDB(DB_PATH)


def _get_level_dir(level: int) -> Path:
    """Return the filesystem directory for a given level."""
    return LEVELS_DIR / f"level_{level}"


def _count_levels() -> int:
    """Count available level directories under server/levels."""
    if not LEVELS_DIR.exists():
        return 0
    count = 0
    for entry in LEVELS_DIR.iterdir():
        if entry.is_dir() and entry.name.startswith("level_"):
            suffix = entry.name.split("level_")[-1]
            if suffix.isdigit():
                count += 1
    return count


def _load_subject(level: int) -> str:
    """Load subject text for the given level."""
    path = _get_level_dir(level) / "subject.en.txt"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return path.read_text(encoding="utf-8")


def _load_starter_files(level: int) -> List[StarterFile]:
    """Load starter files for a level (unused by client)."""
    starter_dir = _get_level_dir(level) / "starter"
    files: List[StarterFile] = []
    if not starter_dir.exists():
        return files
    for path in starter_dir.rglob("*"):
        if path.is_file():
            rel = path.relative_to(starter_dir).as_posix()
            files.append(StarterFile(path=rel, content=path.read_text(encoding="utf-8")))
    return files


def _load_testspec(level: int) -> TestSpec:
    """Load and validate the JSON testspec for a level."""
    path = _get_level_dir(level) / "testspec.json"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testspec not found")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    try:
        return TestSpec(**data)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid testspec")


def _require_protocol(identity: Identity) -> None:
    """Ensure the client protocol version is supported."""
    if identity.protocol_version != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported protocol version")


@app.post("/v1/sync", response_model=SyncResponse)
async def sync(identity: Identity, _sig: dict = Depends(verify_request_signature)) -> SyncResponse:
    """Create/update the user and return their current level."""
    _require_protocol(identity)
    user = db.get_or_create_user(identity.username, identity.client_id)
    db.update_last_seen(identity.username, identity.timestamp)
    return SyncResponse(level=int(user["level"]), total_levels=_count_levels())


@app.get("/v1/subject", response_model=SubjectResponse)
async def subject(
    username: str = Query(...),
    identity: Identity = Body(...),
    _sig: dict = Depends(verify_request_signature),
) -> SubjectResponse:
    """Return the subject for the user's current level."""
    _require_protocol(identity)
    if username != identity.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username mismatch")
    user = db.get_or_create_user(identity.username, identity.client_id)
    level = int(user["level"])
    return SubjectResponse(
        level=level,
        total_levels=_count_levels(),
        subject=_load_subject(level),
        starter_files=[],
    )


@app.get("/v1/testspec", response_model=TestSpecResponse)
async def testspec(
    username: str = Query(...),
    identity: Identity = Body(...),
    _sig: dict = Depends(verify_request_signature),
) -> TestSpecResponse:
    """Return the testspec for the user's current level."""
    _require_protocol(identity)
    if username != identity.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username mismatch")
    user = db.get_or_create_user(identity.username, identity.client_id)
    level = int(user["level"])
    spec = _load_testspec(level)
    return TestSpecResponse(level=level, testspec=spec, constraints=spec.constraints)


@app.post("/v1/submit", response_model=SubmitResponse)
async def submit(payload: SubmitRequest, _sig: dict = Depends(verify_request_signature)) -> SubmitResponse:
    """Record a submission and advance the user if it passed."""
    _require_protocol(payload.identity)
    username = payload.identity.username
    user = db.get_or_create_user(username, payload.identity.client_id)
    level = int(user["level"])
    results = payload.results
    if results.level != level:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Level mismatch")

    passed = bool(results.pass_)
    passed_count = sum(1 for t in results.tests if t.pass_)
    total = len(results.tests)
    summary = f"{passed_count}/{total} tests passed"

    db.record_attempt(
        username=username,
        level=level,
        submitted_at=payload.identity.timestamp or now_iso(),
        passed=passed,
        summary=summary,
        details=payload.dict(by_alias=True),
    )

    new_level = level
    if passed:
        new_level = db.increment_level(username)

    feedback = "Great job!" if passed else "Keep trying."
    return SubmitResponse(level=new_level, feedback=f"{feedback} {summary}.")


@app.get("/v1/admin/users", response_model=AdminUsersResponse)
async def admin_users(x_admin_token: str = Header(default="")) -> AdminUsersResponse:
    """Return a list of users and levels (admin-only)."""
    token = os.getenv("ADMIN_TOKEN")
    if not token or x_admin_token != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    data = db.load()
    users = [AdminUser(username=name, level=int(info.get("level", 1))) for name, info in data.get("users", {}).items()]
    return AdminUsersResponse(users=users)
