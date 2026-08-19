import logging
from pathlib import Path
from openai import OpenAI

from src.backend.assistant.stt.exceptions import (
    TranscriptionError,
    AudioValidationError,
)
from src.backend.core.constants import STT
from src.backend.core.setting import Settings

logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(
        self,
        model_name: str = STT.MODEL_NAME,
        language: str = STT.LANGUAGE,
    ):
        self.model_name = model_name
        self.language = language
        self.client = OpenAI(api_key=Settings.OPENAI_API_KEY)

    def transcribe(self, audio_path: Path) -> str:
        """Transcribes the given audio file using the OpenAI API and returns the text."""
        if not audio_path.exists():
            raise AudioValidationError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing audio file via OpenAI API: {audio_path}")
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    language=self.language,
                )

            text = transcription.text.strip()
            if not text:
                logger.warning("Transcription resulted in empty text.")
                return ""

            return text

        except Exception as error:
            logger.exception("Error during OpenAI transcription.")
            raise TranscriptionError(
                "Failed to transcribe audio via OpenAI."
            ) from error
