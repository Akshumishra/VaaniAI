import logging

from src.backend.core.constants import Paths
from src.backend.core.setting import Settings


def setup_logging():
    Paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = Paths.LOGS_DIR / "app.log"
    
    logging.basicConfig(
        level=getattr(logging, Settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
