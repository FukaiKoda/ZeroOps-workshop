from typing import Dict, Any, List
import httpx
from utils.config import settings


class ZeroOpsClient:
    def __init__(self):
        self.base_url = settings.ZEROOPS_SERVER_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {settings.SESSION_TOKEN}"}

    async def get_me(self) -> Dict[str, Any]:
        try:
            response = await self.client.get("/v1/me", headers=self._auth_headers())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": True, "message": f"Connection error: {e}"}

    async def get_next_exercise(self) -> Dict[str, Any]:
        try:
            response = await self.client.get("/v1/exercise", headers=self._auth_headers())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": True, "message": f"Failed to load exercise: {e}"}

    async def get_exercise_details(self, exercise_slug: str) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/exercises/{exercise_slug}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": True, "message": f"Error loading subject: {e}"}

    async def submit_exercise(self, exercise_slug: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
        payload = {
            "session_token": settings.SESSION_TOKEN,
            "exercise_slug": exercise_slug,
            "files": files,
            "client_version": settings.CLIENT_VERSION,
        }
        try:
            response = await self.client.post("/v1/submit", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": True, "message": f"Submission failed: {str(e)}"}

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/status/{job_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": True, "message": f"Status check failed: {e}"}

    async def close(self):
        await self.client.aclose()
