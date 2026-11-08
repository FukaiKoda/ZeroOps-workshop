"""
GitHub OAuth helper functions.
Handles the OAuth authorization URL, code exchange and GitHub API calls.
Never stores or accepts Personal Access Tokens — OAuth tokens only.
"""

import httpx
from urllib.parse import urlencode
from typing import Optional
from .config import settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"
INTRA_AUTHORIZE_URL = "https://api.intra.42.fr/oauth/authorize"
INTRA_TOKEN_URL = "https://api.intra.42.fr/oauth/token"
INTRA_API_BASE = "https://api.intra.42.fr/v2"

# Scopes: read user info, read emails, and repo access for ownership verification
OAUTH_SCOPES = "read:user user:email repo"


def build_auth_url(state: str, redirect_uri: Optional[str] = None) -> str:
    """
    Build the GitHub OAuth authorization URL.
    The user is redirected here in their browser to authorize the app.
    """
    if not redirect_uri:
        redirect_uri = f"http://localhost:{settings.PORT}/v1/auth/callback"
    params = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": OAUTH_SCOPES,
        "state": state,
    })
    return f"{GITHUB_AUTHORIZE_URL}?{params}"


def build_intra_auth_url(state: str, redirect_uri: Optional[str] = None) -> str:
    """Build the 42 Intra OAuth authorization URL."""
    if not redirect_uri:
        redirect_uri = settings.INTRA_REDIRECT_URI
    params = urlencode({
        "client_id": settings.INTRA_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "public",
        "state": state,
    })
    return f"{INTRA_AUTHORIZE_URL}?{params}"


async def exchange_code_for_token(code: str, redirect_uri: Optional[str] = None) -> Optional[str]:
    """
    Exchange an OAuth authorization code for an access token.
    Returns the token string or None if the exchange fails.
    """
    if not redirect_uri:
        redirect_uri = f"http://localhost:{settings.PORT}/v1/auth/callback"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=10.0,
        )
        data = response.json()
        return data.get("access_token")


async def exchange_intra_code_for_token(code: str, redirect_uri: Optional[str] = None) -> Optional[str]:
    """Exchange a 42 Intra authorization code for an access token."""
    if not redirect_uri:
        redirect_uri = settings.INTRA_REDIRECT_URI
    async with httpx.AsyncClient() as client:
        response = await client.post(
            INTRA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.INTRA_CLIENT_ID,
                "client_secret": settings.INTRA_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=10.0,
        )
        if response.status_code >= 400:
            return None
        return response.json().get("access_token")


async def get_github_user(token: str) -> Optional[dict]:
    """
    Fetch the authenticated user's GitHub profile.
    Returns a dict with id, login, avatar_url, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        return None


async def get_intra_user(token: str) -> Optional[dict]:
    """Fetch the authenticated 42 Intra user's public profile."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INTRA_API_BASE}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        return None


async def get_github_primary_email(token: str) -> Optional[str]:
    """
    Fetch the authenticated user's primary verified email address.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user/emails",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )
        if response.status_code != 200:
            return None

        emails = response.json()
        # Prefer primary + verified email
        for email_obj in emails:
            if email_obj.get("primary") and email_obj.get("verified"):
                return email_obj["email"]
        # Fallback: any verified email
        for email_obj in emails:
            if email_obj.get("verified"):
                return email_obj["email"]
        return None
