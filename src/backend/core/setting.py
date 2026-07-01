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
    OPEN_API_KEY = os.getenv("OPEN_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    WEATHER_API = os.getenv("WEATHER_API")
    TAVILY_API = os.getenv("TAVILY_API")
    WEATHER_URL = os.getenv("WEATHER_URL")
    TAVILY_URL = os.getenv("TAVILY_URL")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        if not cls.HF_TOKEN:
            logger.warning("HF_TOKEN is not set in the environment.")
        if not cls.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set in the environment.")

Settings.validate()
