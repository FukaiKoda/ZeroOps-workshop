from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "zeroops"
    CONFIG_DIR: Path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "zeroops"
    DATABASE_URL: str = "sqlite:///./zeroops.db"
    EXERCISES_DIR: Path = Path("data/exercises")
    
    def model_post_init(self, __context):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.DATABASE_URL = f"sqlite:///{self.DATA_DIR}/zeroops.db"
        self.EXERCISES_DIR = self.DATA_DIR / "exercises"

    class Config:
        env_prefix = "ZEROOPS_"

def load_config() -> Settings:
    return Settings()

settings = load_config()
