import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Dict, Optional
from ..core.database import db
from ..models.user import UserProfile

router = APIRouter()

# Constants
from ..core.config import settings

# Constants
UID = "u-s4t2ud-96a7aa923a38cb7c3b2724cf5664466d19d1d584c92ebdfa6298b1e9021c664a"
SECRET = "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"
# REDIRECT_URI is now dynamic
AUTH_URL = "https://api.intra.42.fr/oauth/authorize"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
API_ME_URL = "https://api.intra.42.fr/v2/me"

# Simple in-memory storage for pending authentications
# state -> user_info (dict)
PENDING_AUTH: Dict[str, dict] = {}

@router.get("/auth/login")
async def login(state: str = Query(..., description="Unique client state for polling")):
    """Redirects the user to 42 API for authentication with a state parameter."""
    # Manually construct URL to ensure correct encoding/formatting
    # We pass the 'state' to 42 API, which will return it in the callback
    redirect_uri = f"{settings.PUBLIC_URL}/v1/auth/callback"
    url = f"{AUTH_URL}?client_id={UID}&redirect_uri={redirect_uri}&response_type=code&state={state}"
    return RedirectResponse(url)

@router.get("/auth/poll")
async def poll_auth(state: str):
    """
    Checks if the authentication for the given state is complete.
    Returns the user info if complete, otherwise returns status: pending.
    """
    if state in PENDING_AUTH:
        user_data = PENDING_AUTH.pop(state) # Consume the event
        return {"status": "success", "user": user_data}
    return {"status": "pending"}

@router.get("/auth/callback")
async def callback(code: str, state: str = Query(None)):
    """Exchanges code for token, gets user info, and stores it mapped to state."""
    async with httpx.AsyncClient() as client:
        # 1. Exchange Code for Token
        redirect_uri = f"{settings.PUBLIC_URL}/v1/auth/callback"
        token_resp = await client.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": UID,
            "client_secret": SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
            "state": state
        })
        
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to retrieve access token: {token_resp.text}")
            
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        
        # 2. Get User Info
        me_resp = await client.get(API_ME_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        if me_resp.status_code != 200:
             raise HTTPException(status_code=400, detail="Failed to retrieve user info")
             
        user_data = me_resp.json()
        login = user_data.get("login")
        
        # 3. Create or Update User in DB
        user = db.get_user(login)
        if not user:
            user = UserProfile(user_id=login)
            db.save_user(user)

        # 4. Store result for the polling client
        if state:
            PENDING_AUTH[state] = {
                "user_id": login,
                "token": access_token # We might not need this on client, but good to have
            }

        # 5. Display Success Page
        html_content = f"""
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{ font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #121212; color: #ffffff; }}
                    .success {{ color: #4caf50; font-size: 24px; }}
                    .info {{ margin-top: 20px; font-size: 18px; }}
                    code {{ background-color: #333; padding: 5px 10px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1 class="success">✅ Authentication Successful</h1>
                <p class="info">Welcome, <strong>{login}</strong>!</p>
                <p>You have been successfully logged in.</p>
                <p>Check your terminal! The application should continue automatically.</p>
                <script>
                    // Optional: Close window after a delay
                    setTimeout(function() {{ window.close(); }}, 3000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
