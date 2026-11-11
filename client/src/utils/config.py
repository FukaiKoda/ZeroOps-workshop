import os
import getpass
import socket
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the client package
_CLIENT_DIR = Path(__file__).resolve().parent.parent.parent

# Workshop identity keeps credentials isolated between workshop deployments.
_KEYRING_SERVICE = "zeroops"
_KEYRING_USERNAME = "session_token"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_CLIENT_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Keep local development usable when no client/.env has been created yet.
    ZEROOPS_SERVER_URL: str = "http://localhost:8000"
    ZEROOPS_WORKSHOP_ID: str = "git"

    # Legacy fields — kept for compatibility; USER_ID now comes from GitHub profile
    USER_ID: str = getpass.getuser()
    HOSTNAME: str = socket.gethostname()
    CWD: str = os.getcwd()
    RENDU_DIR: Path = Path.home() / "rendudevops"

    # Token storage path (fallback when keyring is unavailable)
    TOKEN_FILE: Path | None = None
    DEBUG_LOG_FILE: Path = Path.home() / ".zeroops" / "debug.log"

    def model_post_init(self, context, /):
        if self.TOKEN_FILE is None:
            self.TOKEN_FILE = (
                Path.home()
                / ".config"
                / "zeroops"
                / self.ZEROOPS_WORKSHOP_ID
                / "token"
            )


settings = Settings()


def log_debug(message: str) -> None:
    """Safely append debug logs to user-isolated ~/.zeroops/debug.log."""
    try:
        settings.DEBUG_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.DEBUG_LOG_FILE, "a") as f:
            f.write(f"{message}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Token helpers — keyring preferred, file fallback
# ---------------------------------------------------------------------------

def load_token() -> str | None:
    """Load the stored session JWT. Returns None if not found."""
    # Try keyring first
    try:
        import keyring
        token = keyring.get_password(_KEYRING_SERVICE, _token_key())
        if token:
            return token
    except Exception:
        pass

    # Fallback: plain file
    try:
        if settings.TOKEN_FILE and settings.TOKEN_FILE.exists():
            return settings.TOKEN_FILE.read_text().strip() or None
    except Exception:
        pass

    return None


def save_token(token: str) -> None:
    """Persist the session JWT securely."""
    # Try keyring first
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _token_key(), token)
        return
    except Exception:
        pass

    # Fallback: write to file
    try:
        if settings.TOKEN_FILE:
            settings.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            settings.TOKEN_FILE.write_text(token)
    except Exception as e:
        print(f"Warning: could not save token: {e}")


def clear_token() -> None:
    """Remove the stored session JWT on logout."""
    try:
        import keyring
        keyring.delete_password(_KEYRING_SERVICE, _token_key())
    except Exception:
        pass

    try:
        if settings.TOKEN_FILE and settings.TOKEN_FILE.exists():
            settings.TOKEN_FILE.unlink()
    except Exception:
        pass


def _token_key() -> str:
    return f"{settings.ZEROOPS_WORKSHOP_ID}:{_KEYRING_USERNAME}"
