"""
GitHub OAuth authentication endpoints.

Flow:
  1. GET  /v1/auth/login        → returns {auth_url, state}; client opens browser
  2. GET  /v1/auth/callback     → GitHub redirects here; server exchanges code, upserts user
  3. GET  /v1/auth/poll/{state} → client polls until status == "complete"
  4. GET  /v1/auth/me           → client fetches own profile using JWT
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..core.oauth import build_auth_url, exchange_code_for_token, get_github_user, get_github_primary_email
from ..core.session import create_state_token, complete_state, poll_state, create_session_token, verify_session_token
from ..core.rate_limit import limiter
from ..models.db_user import User
from ..models.auth import LoginInitResponse, PollResponse, UserProfileResponse, RepositoryInfo

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Dependency: get current user from JWT Bearer token
# ---------------------------------------------------------------------------

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    FastAPI dependency. Reads Authorization: Bearer <token> header,
    validates the JWT, and returns the User ORM object.
    Raises 401 if token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")

    token = auth_header.removeprefix("Bearer ").strip()
    user_id = verify_session_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")

    return user


# ---------------------------------------------------------------------------
# Step 1: Initiate login
# ---------------------------------------------------------------------------

@router.get("/login", response_model=LoginInitResponse)
@limiter.limit("20/minute")
async def initiate_login(request: Request):
    """
    Returns a GitHub OAuth authorization URL and a state token.
    The client opens the URL in the system browser and polls /poll/{state}.
    """
    state = create_state_token()
    auth_url = build_auth_url(state)
    return LoginInitResponse(auth_url=auth_url, state=state)


# ---------------------------------------------------------------------------
# Step 2: OAuth callback (GitHub redirects here)
# ---------------------------------------------------------------------------

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    GitHub redirects to this endpoint after the user authorizes the app.
    Exchanges the code for a token, upserts the user, and marks the state complete.
    Returns an HTML page the browser can display while the TUI resumes.
    """
    # Exchange code for OAuth token
    access_token = await exchange_code_for_token(code)
    if not access_token:
        return HTMLResponse(
            _html_result("Authentication Failed", "Could not exchange code for token.", False),
            status_code=400,
        )

    # Fetch GitHub user info
    github_user = await get_github_user(access_token)
    if not github_user:
        return HTMLResponse(
            _html_result("Authentication Failed", "Could not fetch GitHub user info.", False),
            status_code=400,
        )

    github_email = await get_github_primary_email(access_token)

    # Upsert user in database
    user = await _upsert_user(db, github_user, github_email, access_token)

    # Create JWT session token for the client
    session_token = create_session_token(user.id)

    # Mark state as complete so the polling client can pick it up
    complete_state(state, session_token)

    return HTMLResponse(
        _html_result(
            "Authorization Successful!",
            f"Welcome, @{user.github_username}! You can close this tab and return to the terminal.",
            True,
        )
    )


# ---------------------------------------------------------------------------
# Step 3: Polling endpoint (TUI client polls this)
# ---------------------------------------------------------------------------

@router.get("/poll/{state}", response_model=PollResponse)
@limiter.limit("60/minute")
async def poll_auth(state: str, request: Request):
    """
    The TUI client polls this endpoint every 2 seconds after opening the browser.
    Returns {status: "pending"} until the user completes OAuth in the browser,
    then returns {status: "complete", token: "<jwt>"}.
    """
    result = poll_state(state)
    return PollResponse(status=result["status"], token=result.get("token"))


# ---------------------------------------------------------------------------
# Step 4: Current user profile (requires JWT)
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserProfileResponse)
@limiter.limit("120/minute")
async def get_me(request: Request, current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's full profile including linked repository."""
    return _build_profile_response(current_user)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _upsert_user(
    db: AsyncSession,
    github_user: dict,
    github_email: str | None,
    access_token: str,
) -> User:
    """
    Insert a new user or update an existing one matched by github_id.
    Link by email is handled naturally: if the email already exists on another
    account, the github_id uniqueness constraint will prevent duplicate creation.
    """
    github_id = github_user["id"]

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=github_id,
            github_username=github_user.get("login", ""),
            github_avatar=github_user.get("avatar_url", ""),
            github_email=github_email,
            access_token=access_token,
        )
        db.add(user)
    else:
        # Refresh mutable fields on subsequent logins
        user.github_username = github_user.get("login", user.github_username)
        user.github_avatar = github_user.get("avatar_url", user.github_avatar)
        user.github_email = github_email or user.github_email
        user.access_token = access_token  # Always refresh token

    await db.commit()
    await db.refresh(user)
    return user


def _build_profile_response(user: User) -> UserProfileResponse:
    repo_info = None
    if user.repository:
        r = user.repository
        repo_info = RepositoryInfo(
            owner=r.owner,
            repo=r.repo,
            full_name=r.full_name,
            default_branch=r.default_branch,
            last_commit_hash=r.last_commit_hash,
            last_synced_at=r.last_synced_at,
        )

    return UserProfileResponse(
        id=user.id,
        github_id=user.github_id,
        github_username=user.github_username,
        github_avatar=user.github_avatar or "",
        github_email=user.github_email,
        current_level=user.current_level,
        total_xp=user.total_xp,
        has_repository=user.repository is not None,
        repository=repo_info,
        created_at=user.created_at,
    )


def _html_result(title: str, message: str, success: bool) -> str:
    color = "#22c55e" if success else "#ef4444"
    icon = "✅" if success else "❌"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>ZeroOps — {title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0d1117; color: #e6edf3;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh;
    }}
    .card {{
      background: #161b22; border: 1px solid #30363d; border-radius: 12px;
      padding: 40px 48px; max-width: 480px; width: 100%; text-align: center;
    }}
    .icon {{ font-size: 48px; margin-bottom: 16px; }}
    h1 {{ font-size: 24px; font-weight: 600; color: {color}; margin-bottom: 12px; }}
    p {{ font-size: 15px; color: #8b949e; line-height: 1.6; }}
    .brand {{ margin-top: 32px; font-size: 13px; color: #484f58; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <p class="brand">ZeroOps Workshop Platform</p>
  </div>
</body>
</html>"""
