import os
import getpass
import socket
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MANUALLY SET THIS TO YOUR HOST IP (e.g., http://192.168.1.15:8000)
    ZEROOPS_SERVER_URL: str = "http://localhost:8000"
    
    # Environment info
    USER_ID: str = getpass.getuser()
    HOSTNAME: str = socket.gethostname()
    CWD: str = os.getcwd()
    RENDU_DIR: Path = Path.home() / "rendudevops"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
