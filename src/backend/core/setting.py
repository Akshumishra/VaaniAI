import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Resolve project root (assuming this is in Backend/src/settings.py)
project_root = Path(__file__).resolve().parent.parent.parent
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Loaded .env file.")
else:
    logger.warning(f"No .env file found at {env_path}.")

class Settings:
    """Global configuration settings."""
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    @classmethod
    def validate(cls):
        if not cls.HF_TOKEN:
            logger.warning("HF_TOKEN is not set in the environment.")

Settings.validate()
