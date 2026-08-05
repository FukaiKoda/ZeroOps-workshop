import httpx
from typing import Dict, Any, Optional
from utils.config import settings, load_token
from utils.executor import LocalGrader


class ZeroOpsClient:
    def __init__(self):
        self.base_url = settings.ZEROOPS_SERVER_URL
        token = load_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=15.0,
        )

    # -----------------------------------------------------------------------
    # Auth
    # -----------------------------------------------------------------------

    async def initiate_login(self) -> Dict[str, Any]:
        """Request a GitHub OAuth URL and state token from the server."""
        try:
            response = await self.client.get("/v1/auth/login")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}

    async def poll_login(self, state: str) -> Dict[str, Any]:
        """
        Poll the server for OAuth completion.
        Returns {status: "pending"|"complete"|"expired", token: str|None}.
        """
        try:
            response = await self.client.get(f"/v1/auth/poll/{state}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"status": "error", "error": str(e)}

    async def get_me(self) -> Dict[str, Any]:
        """Fetch the authenticated user's GitHub profile and repository info."""
        try:
            response = await self.client.get("/v1/auth/me")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}

    # -----------------------------------------------------------------------
    # Repository
    # -----------------------------------------------------------------------

    async def get_linked_repo(self) -> Optional[Dict[str, Any]]:
        """Get the user's linked GitHub repository info. Returns None if not linked."""
        try:
            response = await self.client.get("/v1/repo/me")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def link_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Link an existing GitHub repository. Ownership is verified server-side."""
        try:
            response = await self.client.post(
                "/v1/repo/link", json={"owner": owner, "repo": repo}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            return {"status": "error", "message": detail}
        except httpx.HTTPError as e:
            return {"status": "error", "message": str(e)}

    async def sync_repo(self) -> Dict[str, Any]:
        """Trigger a repository synchronization — verifies existence, fetches latest commit."""
        try:
            response = await self.client.post("/v1/repo/sync")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            return {"status": "error", "message": detail}
        except httpx.HTTPError as e:
            return {"status": "error", "message": str(e)}

    # -----------------------------------------------------------------------
    # Exercises
    # -----------------------------------------------------------------------

    async def get_status(self) -> Dict[str, Any]:
        try:
            # Fetch profile to get user identity
            me = await self.get_me()
            username = me.get("github_username", settings.USER_ID)
            response = await self.client.get(f"/v1/status/{username}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"status": "error", "message": f"Connection error: {e}"}

    async def get_exercise_details(self, exercise_id: str) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/exercises/{exercise_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "id": exercise_id,
                "subject": f"Error loading subject: {e}",
                "points": 0,
            }

    async def get_leaderboard(self) -> list[Dict[str, Any]]:
        try:
            response = await self.client.get("/v1/leaderboard")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return []

    async def get_submissions(self) -> list[Dict[str, Any]]:
        """Get the authenticated user's full submission history."""
        try:
            response = await self.client.get("/v1/submissions/me")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return []

    async def submit_exercise(self, exercise_id: str, code: str = "", commit_hash: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "user_id": settings.USER_ID,
            "exercise_id": exercise_id,
            "code": code,
            "commit_hash": commit_hash,
        }
        try:
            response = await self.client.post("/v1/grade", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "pending" and "script_content" in data:
                script = data["script_content"]
                nonce = data["nonce"]

                target_dir = settings.RENDU_DIR / exercise_id

                success, logs = LocalGrader.execute_script(
                    script, nonce, target_dir=target_dir
                )

                verify_payload = {
                    "user_id": settings.USER_ID,
                    "nonce": nonce,
                    "result": success,
                    "logs": logs,
                    "commit_hash": commit_hash,
                }

                verify_response = await self.client.post(
                    "/v1/verify", json=verify_payload
                )
                verify_response.raise_for_status()
                return verify_response.json()

            return data

        except httpx.HTTPError as e:
            return {
                "status": "error",
                "message": f"Submission failed: {str(e)}",
                "new_level": -1,
                "score": 0,
            }

    async def close(self):
        await self.client.aclose()
