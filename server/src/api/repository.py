"""
Repository management endpoints.

POST /v1/repo/link  — Link an existing GitHub repository (ownership verified)
GET  /v1/repo/me    — Get the current user's linked repository
POST /v1/repo/sync  — Sync the repository (verify existence, fetch latest commit)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.rate_limit import limiter
from ..core.github_repo import (
    verify_repo_exists,
    verify_repo_ownership,
    get_repo_info,
    get_latest_commit,
    list_repo_top_level_dirs,
)
from ..models.db_user import User
from ..models.db_repository import Repository
from ..models.auth import RepositoryInfo
from .auth import get_current_user

router = APIRouter(prefix="/repo", tags=["repository"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LinkRepoRequest(BaseModel):
    owner: str
    repo: str


class LinkRepoResponse(BaseModel):
    status: str
    message: str
    repository: RepositoryInfo | None = None


class SyncResponse(BaseModel):
    status: str
    message: str
    commit_hash: str | None = None
    last_synced_at: datetime | None = None
    exercise_folders: list[str] = []


# ---------------------------------------------------------------------------
# GET /v1/repo/me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=RepositoryInfo | None)
@limiter.limit("120/minute")
async def get_my_repository(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Returns the linked repository for the authenticated user, or null."""
    if not current_user.repository:
        return None

    r = current_user.repository
    return RepositoryInfo(
        owner=r.owner,
        repo=r.repo,
        full_name=r.full_name,
        default_branch=r.default_branch,
        last_commit_hash=r.last_commit_hash,
        last_synced_at=r.last_synced_at,
    )


# ---------------------------------------------------------------------------
# POST /v1/repo/link
# ---------------------------------------------------------------------------

@router.post("/link", response_model=LinkRepoResponse)
@limiter.limit("10/minute")
async def link_repository(
    request: Request,
    body: LinkRepoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Link an existing GitHub repository to the authenticated user.

    Security checks:
      1. Repository must exist and be accessible.
      2. Authenticated user must be the owner or have admin access.
         This prevents students from linking repos they don't own.
    """
    owner = body.owner.strip()
    repo = body.repo.strip()

    if not owner or not repo:
        raise HTTPException(status_code=422, detail="owner and repo must not be empty.")

    # Security: verify repository exists
    if not await verify_repo_exists(owner, repo, current_user.access_token):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{owner}/{repo}' not found or not accessible.",
        )

    # Security: verify ownership — prevent linking someone else's repo
    is_owner = await verify_repo_ownership(
        owner, repo, current_user.github_username, current_user.access_token
    )
    if not is_owner:
        raise HTTPException(
            status_code=403,
            detail=(
                f"You do not have ownership or admin access to '{owner}/{repo}'. "
                "Only link repositories you own."
            ),
        )

    # Fetch default branch from GitHub
    info = await get_repo_info(owner, repo, current_user.access_token)
    default_branch = info.get("default_branch", "main") if info else "main"

    # Upsert repository record
    if current_user.repository:
        # Update existing link
        current_user.repository.owner = owner
        current_user.repository.repo = repo
        current_user.repository.default_branch = default_branch
        current_user.repository.last_commit_hash = None
        current_user.repository.last_synced_at = None
        repository = current_user.repository
    else:
        repository = Repository(
            user_id=current_user.id,
            owner=owner,
            repo=repo,
            default_branch=default_branch,
        )
        db.add(repository)

    await db.commit()
    await db.refresh(repository)

    return LinkRepoResponse(
        status="linked",
        message=f"Repository '{owner}/{repo}' linked successfully.",
        repository=RepositoryInfo(
            owner=repository.owner,
            repo=repository.repo,
            full_name=repository.full_name,
            default_branch=repository.default_branch,
            last_commit_hash=repository.last_commit_hash,
            last_synced_at=repository.last_synced_at,
        ),
    )


# ---------------------------------------------------------------------------
# POST /v1/repo/sync
# ---------------------------------------------------------------------------

@router.post("/sync", response_model=SyncResponse)
@limiter.limit("30/minute")
async def sync_repository(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synchronise the linked repository:
      - Verify the repository still exists
      - Fetch the latest commit hash on the default branch
      - List top-level exercise folders
      - Update last_commit_hash and last_synced_at
    """
    if not current_user.repository:
        raise HTTPException(
            status_code=404,
            detail="No repository linked. Use POST /v1/repo/link first.",
        )

    r = current_user.repository
    token = current_user.access_token

    # Verify repository still exists
    if not await verify_repo_exists(r.owner, r.repo, token):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{r.full_name}' no longer exists or is not accessible.",
        )

    # Fetch latest commit
    commit_hash = await get_latest_commit(r.owner, r.repo, r.default_branch, token)

    # List exercise folders found in the repo root
    exercise_folders = await list_repo_top_level_dirs(r.owner, r.repo, token)

    # Update sync state
    now = datetime.now(timezone.utc)
    r.last_commit_hash = commit_hash
    r.last_synced_at = now

    await db.commit()

    return SyncResponse(
        status="synced",
        message=f"Repository '{r.full_name}' synced successfully.",
        commit_hash=commit_hash,
        last_synced_at=now,
        exercise_folders=exercise_folders,
    )


# ---------------------------------------------------------------------------
# Future extension point: POST /v1/repo/create (from template)
# ---------------------------------------------------------------------------
# When a GitHub template repository is available, add:
#
# @router.post("/create", response_model=LinkRepoResponse)
# async def create_from_template(...):
#     repo_data = await create_repo_from_template(...)
#     ...
