"""
GitHub Repository API wrapper.
Used by the sync and repository linking endpoints to verify ownership
and fetch commit metadata without requiring a PAT.
All calls use the user's stored OAuth token.
"""

import httpx
from typing import Optional

GITHUB_API_BASE = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def verify_repo_exists(owner: str, repo: str, token: str) -> bool:
    """Check that a repository exists and is accessible with the given token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=_headers(token),
            timeout=10.0,
        )
        return response.status_code == 200


async def get_repo_info(owner: str, repo: str, token: str) -> Optional[dict]:
    """
    Fetch repository metadata.
    Returns a dict with: full_name, default_branch, private, owner.login, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=_headers(token),
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        return None


async def verify_repo_ownership(
    owner: str, repo: str, github_username: str, token: str
) -> bool:
    """
    Verify the authenticated user owns or has admin access to the repository.
    Security: prevents students from linking repos they don't own.
    Checks: repo owner matches username OR user has admin permission.
    """
    info = await get_repo_info(owner, repo, token)
    if not info:
        return False

    # Direct ownership check
    repo_owner = info.get("owner", {}).get("login", "").lower()
    if repo_owner == github_username.lower():
        return True

    # Check permissions (for org repos where user might be admin)
    permissions = info.get("permissions", {})
    return permissions.get("admin", False)


async def get_latest_commit(owner: str, repo: str, branch: str, token: str) -> Optional[str]:
    """
    Get the SHA of the latest commit on the specified branch.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{branch}",
            headers=_headers(token),
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json().get("sha")
        return None


async def list_repo_top_level_dirs(owner: str, repo: str, token: str) -> list[str]:
    """
    List top-level directories in the repository root.
    Used to verify exercise folders exist.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/",
            headers=_headers(token),
            timeout=10.0,
        )
        if response.status_code != 200:
            return []
        contents = response.json()
        return [
            item["name"]
            for item in contents
            if isinstance(item, dict) and item.get("type") == "dir"
        ]


async def verify_exercise_folder_exists(
    owner: str, repo: str, exercise_id: str, token: str
) -> bool:
    """
    Check whether a specific exercise folder (e.g., ex01_docker_coming_soon)
    exists in the repository.
    """
    dirs = await list_repo_top_level_dirs(owner, repo, token)
    return exercise_id in dirs


async def fetch_directory(
    owner: str, repo: str, directory_path: str, token: str
) -> dict[str, str]:
    """
    Recursively fetch all files inside `directory_path` from the repository.
    Returns a dict mapping relative file path (relative to directory_path) -> string content.
    Uses the GitHub Contents API (base64 encoded blobs).
    """
    import base64

    result: dict[str, str] = {}
    clean_path = directory_path.strip("/")

    async with httpx.AsyncClient() as client:
        async def _fetch_recursive(current_path: str):
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{current_path}"
            resp = await client.get(url, headers=_headers(token), timeout=10.0)
            if resp.status_code != 200:
                return

            items = resp.json()
            if not isinstance(items, list):
                if isinstance(items, dict) and items.get("type") == "file":
                    items = [items]
                else:
                    return

            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                item_path = item.get("path", "")
                if item_type == "dir":
                    await _fetch_recursive(item_path)
                elif item_type == "file":
                    file_url = item.get("url")
                    if not file_url:
                        continue
                    file_resp = await client.get(file_url, headers=_headers(token), timeout=10.0)
                    if file_resp.status_code != 200:
                        continue
                    file_data = file_resp.json()
                    encoding = file_data.get("encoding", "")
                    content_raw = file_data.get("content", "")
                    if encoding == "base64":
                        try:
                            content = base64.b64decode(content_raw).decode("utf-8")
                            rel_path = item_path[len(clean_path):].lstrip("/") if item_path.startswith(clean_path) else item_path
                            result[rel_path] = content
                        except Exception:
                            pass

        await _fetch_recursive(clean_path)

    return result


async def fetch_workflow_files(owner: str, repo: str, token: str) -> dict[str, str]:
    """Fetch all workflow files inside .github/workflows for backward compatibility."""
    return await fetch_directory(owner, repo, ".github/workflows", token)



# ---------------------------------------------------------------------------
# Future extension point: create_repo_from_template
# Implement here when a template repository is available.
# ---------------------------------------------------------------------------
# async def create_repo_from_template(
#     template_owner: str,
#     template_repo: str,
#     new_repo_name: str,
#     owner: str,
#     token: str,
# ) -> Optional[dict]:
#     """Create a new repository from a GitHub template."""
#     ...
