import os
import logging
from dotenv import load_dotenv

from src.backend.core.constants import Paths

logger = logging.getLogger(__name__)

if Paths.ENV_PATH.exists():
    load_dotenv(dotenv_path=Paths.ENV_PATH)
    logger.info("Loaded .env file.")
else:
    logger.warning(f"No .env file found at {Paths.ENV_PATH}.")

class Settings:
    """Global configuration settings."""
    HF_TOKEN = os.getenv("HF_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        if not cls.HF_TOKEN:
            logger.warning("HF_TOKEN is not set in the environment.")

Settings.validate()
