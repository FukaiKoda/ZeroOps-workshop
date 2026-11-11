from pydantic_settings import BaseSettings
from pathlib import Path
import os
import re
import secrets


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    WORKSHOP_ID: str = "git"
    WORKSHOP_REPOSITORY: str = ""

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        / "zeroops"
    )
    CONFIG_DIR: Path = (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "zeroops"
    )

    # Database — SQLite (async)
    DATABASE_URL: str = ""

    # Exercises (served from flat-file JSON, unchanged)
    EXERCISES_DIR: Path = Path("data/exercises")

    # GitHub OAuth App credentials
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/v1/auth/callback"

    # 42 Intra OAuth App credentials
    INTRA_CLIENT_ID: str = ""
    INTRA_CLIENT_SECRET: str = ""
    INTRA_REDIRECT_URI: str = "http://localhost:8000/v1/auth/intra/callback"

    # Secret key for JWT signing and state tokens
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = secrets.token_hex(32)

    # JWT settings
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30

    # Auth state token TTL in seconds (browser OAuth window)
    AUTH_STATE_TTL_SECONDS: int = 300  # 5 minutes

    def model_post_init(self, __context):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.WORKSHOP_ID = re.sub(
            r"[^a-z0-9_-]+", "-", self.WORKSHOP_ID.strip().lower()
        ).strip("-_")
        if not self.WORKSHOP_ID:
            raise ValueError("ZEROOPS_WORKSHOP_ID must not be empty")
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"sqlite+aiosqlite:///{self.DATA_DIR}/{self.WORKSHOP_ID}.db"
            )
        self.EXERCISES_DIR = self.DATA_DIR / "exercises"

    class Config:
        env_prefix = "ZEROOPS_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def load_config() -> Settings:
    return Settings()


settings = load_config()
