"""
Storage: JSON-based user and session storage.

Handles:
- User profiles (data/users/{user_id}.json)
- Session tokens
- File locking for concurrent writes
"""

import json
import fcntl
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from schemas import UserProfile, SessionToken

logger = logging.getLogger(__name__)


class Storage:
    """
    JSON-based storage with file locking.
    
    Directory structure:
    data/users/{user_id}.json - User profiles
    data/sessions/{token}.json - Session tokens (optional)
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize storage."""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
        
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.sessions_dir = self.data_dir / "sessions"
        
        # Create directories if they don't exist
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Storage initialized at {self.data_dir}")

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile or None
        """
        user_file = self.users_dir / f"{user_id}.json"
        if not user_file.exists():
            return None
        
        try:
            with open(user_file, 'r') as f:
                # Acquire shared lock (multiple readers OK)
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
            return UserProfile(**data)
        except Exception as e:
            logger.error(f"❌ Failed to load user {user_id}: {e}")
            return None

    def save_user(self, user: UserProfile):
        """
        Save user to disk.
        
        Args:
            user: UserProfile object
        """
        user_file = self.users_dir / f"{user.user_id}.json"
        
        try:
            # Update timestamp
            user.updated_at = datetime.utcnow()
            
            # Write with exclusive lock
            with open(user_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(user.model_dump(), f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
            logger.debug(f"💾 Saved user {user.user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save user {user.user_id}: {e}")
            raise

    def get_or_create_user(self, session_token: str) -> UserProfile:
        """
        Get user by session token, or create new user.
        
        For simplicity, we use session_token as user_id.
        In production, use HMAC-signed tokens and separate user IDs.
        
        Args:
            session_token: Session token from client
            
        Returns:
            UserProfile
        """
        # Simplified: Use token as user_id (hash it for safety)
        import hashlib
        user_id = hashlib.sha256(session_token.encode()).hexdigest()[:12]
        
        user = self.get_user(user_id)
        if user:
            return user
        
        # Create new user
        logger.info(f"👤 Creating new user: {user_id}")
        user = UserProfile(
            user_id=user_id,
            username=f"user_{user_id[:6]}",
            current_level=0,
            current_exercise_slug="ex00_hello",  # Start at first exercise
            total_score=0,
            history=[],
            last_login_ip="127.0.0.1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.save_user(user)
        return user

    def get_user_by_token(self, token: str) -> Optional[UserProfile]:
        """
        Get user by session token.
        
        Args:
            token: Session token
            
        Returns:
            UserProfile or None
        """
        return self.get_or_create_user(token)

    def list_all_users(self) -> list[UserProfile]:
        """
        List all users (for debugging).
        
        Returns:
            List of UserProfile objects
        """
        users = []
        for user_file in self.users_dir.glob("*.json"):
            user_id = user_file.stem
            user = self.get_user(user_id)
            if user:
                users.append(user)
        return users
