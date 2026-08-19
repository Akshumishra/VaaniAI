import logging
from pathlib import Path

from src.backend.core.constants import Logs


def setup_logging():
    project_root = Path(__file__).resolve().parent.parent.parent
    logs_dir = project_root / Logs.logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / "app.log"
    
    logging.basicConfig(
        level=getattr(logging, Logs.level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
