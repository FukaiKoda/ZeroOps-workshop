import os
import getpass
import socket
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the client package
_CLIENT_DIR = Path(__file__).resolve().parent.parent.parent

# Keyring service name for token storage
_KEYRING_SERVICE = "zeroops"
_KEYRING_USERNAME = "session_token"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_CLIENT_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ZEROOPS_SERVER_URL: str = "http://<ZEROOPS_SERVER_IP>:8000"

    # Legacy fields — kept for compatibility; USER_ID now comes from GitHub profile
    USER_ID: str = getpass.getuser()
    HOSTNAME: str = socket.gethostname()
    CWD: str = os.getcwd()
    RENDU_DIR: Path = Path.home() / "rendudevops"

    # Token storage path (fallback when keyring is unavailable)
    TOKEN_FILE: Path = Path.home() / ".config" / "zeroops" / "token"
    DEBUG_LOG_FILE: Path = Path.home() / ".zeroops" / "debug.log"


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
        token = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        if token:
            return token
    except Exception:
        pass

    # Fallback: plain file
    try:
        if settings.TOKEN_FILE.exists():
            return settings.TOKEN_FILE.read_text().strip() or None
    except Exception:
        pass

    return None


def save_token(token: str) -> None:
    """Persist the session JWT securely."""
    # Try keyring first
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, token)
        return
    except Exception:
        pass

    # Fallback: write to file
    try:
        settings.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings.TOKEN_FILE.write_text(token)
    except Exception as e:
        print(f"Warning: could not save token: {e}")


def clear_token() -> None:
    """Remove the stored session JWT on logout."""
    try:
        import keyring
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        pass

    try:
        if settings.TOKEN_FILE.exists():
            settings.TOKEN_FILE.unlink()
    except Exception:
        pass
