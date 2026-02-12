from pydantic_settings import BaseSettings
from pathlib import Path
import os
import yaml

class Settings(BaseSettings):
    # Core Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    PUBLIC_URL: str = os.environ.get("ZEROOPS_PUBLIC_URL", "http://localhost:8000") # Must match 42 App Redirect URI
    
    # Paths (XDG Compliant Defaults)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # Data Directory (DB, Exercises)
    # Default: ~/.local/share/zeroops
    DATA_DIR: Path = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "zeroops"
    
    # Config Directory
    # Default: ~/.config/zeroops
    CONFIG_DIR: Path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "zeroops"

    # Computed Paths
    DATABASE_URL: str = "sqlite:///./zeroops.db" # Will be updated in __init__
    EXERCISES_DIR: Path = Path("data/exercises") # Will be updated
    
    def model_post_init(self, __context):
        # Ensure directories exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Update paths based on DATA_DIR
        self.DATABASE_URL = f"sqlite:///{self.DATA_DIR}/zeroops.db"
        self.EXERCISES_DIR = self.DATA_DIR / "exercises"

    class Config:
        env_prefix = "ZEROOPS_"

def load_config() -> Settings:
    # 1. Load from env var or XDG location
    config_path = os.environ.get("ZEROOPS_CONFIG")
    if not config_path:
        config_path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "zeroops" / "server.yaml"
    else:
        config_path = Path(config_path)
    
    settings_kwargs = {}
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    settings_kwargs.update(config_data)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            
    # Allow Environment Variables to override YAML (Manual Override)
    if "ZEROOPS_PUBLIC_URL" in os.environ:
        settings_kwargs["PUBLIC_URL"] = os.environ["ZEROOPS_PUBLIC_URL"]
        
    return Settings(**settings_kwargs)

settings = load_config()
