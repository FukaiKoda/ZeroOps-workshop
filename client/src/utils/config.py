import os
import getpass
import socket
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ZEROOPS_SERVER_URL: str = "http://127.0.0.1:8000"
    
    # Environment info
    USER_ID: str = getpass.getuser()
    HOSTNAME: str = socket.gethostname()
    CWD: str = os.getcwd()
    RENDU_DIR: Path = Path.home() / "rendudevops"

    class Config:
        env_file = ".env"

settings = Settings()
