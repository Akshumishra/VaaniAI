import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.backend.services.assistant_service import VoiceAssistant
from src.backend.core.setting import Settings

def main():
    print("Starting VaaniAI application...")
    logging.basicConfig(
        level=getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    assistant = VoiceAssistant()
    assistant.run_continuous_loop()

if __name__ == "__main__":
    main()
