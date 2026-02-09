import httpx
from typing import Optional, Dict, Any
from utils.config import settings

from utils.executor import LocalGrader

class ZeroOpsClient:
    def __init__(self):
        self.base_url = settings.ZEROOPS_SERVER_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)

    async def get_status(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/status/{settings.USER_ID}")
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
             return {"id": exercise_id, "subject": f"Error loading subject: {e}", "points": 0}

    async def get_leaderboard(self) -> list[Dict[str, Any]]:
        try:
            response = await self.client.get("/v1/leaderboard")
            response.json() # Verify it renders
            return response.json()
        except httpx.HTTPError:
            return []

    async def submit_exercise(self, exercise_id: str, code: str = "") -> Dict[str, Any]:
        payload = {
            "user_id": settings.USER_ID,
            "exercise_id": exercise_id,
            "code": code
        }
        try:
            # 1. Request Grading Script
            response = await self.client.post("/v1/grade", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "pending" and "script_content" in data:
                # 2. Execute Locally
                script = data["script_content"]
                nonce = data["nonce"]
                
                success, logs = LocalGrader.execute_script(script, nonce)
                
                # 3. Verify Result
                verify_payload = {
                    "user_id": settings.USER_ID,
                    "nonce": nonce,
                    "result": success,
                    "logs": logs
                }
                
                verify_response = await self.client.post("/v1/verify", json=verify_payload)
                verify_response.raise_for_status()
                return verify_response.json()
                
            return data
            
        except httpx.HTTPError as e:
            return {"status": "error", "message": f"Submission failed: {str(e)}", "new_level": -1, "score": 0}

    async def poll_auth(self, state: str) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/auth/poll?state={state}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
             return {"status": "error"}

    async def close(self):
        await self.client.aclose()
