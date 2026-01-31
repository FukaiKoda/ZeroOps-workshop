import os
import getpass
import socket
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ZEROOPS_SERVER_URL: str = "http://127.0.0.1:8000"
    CLIENT_VERSION: str = "0.1.0"

    # Session/user info
    USER_ID: str = getpass.getuser()
    SESSION_TOKEN: str = os.getenv("ZEROOPS_SESSION_TOKEN", USER_ID)

    # Environment info
    HOSTNAME: str = socket.gethostname()
    CWD: str = os.getcwd()

    # Workspace
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
    RENDU_DIR: Path = Path.home() / "rendudevops"

    class Config:
        env_file = ".env"


settings = Settings()
