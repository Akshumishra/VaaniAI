import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from faster_whisper import WhisperModel

from src.backend.assistant.stt.exceptions import TranscriptionError, AudioValidationError
from src.backend.core.constants import STT
from src.backend.core.setting import Settings

logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(
        self,
        model_name: str = STT.MODEL_NAME,
        device: str = STT.DEVICE,
        language: str = STT.LANGUAGE,
        task: str = STT.TASK,
    ):
        self.model_name = model_name
        self.device = device
        self.language = language
        self.task = task
        self.model = None
        self._hf_token = Settings.HF_TOKEN

    def _load_model(self) -> None:
        """Load Whisper model on GPU first, fall back to CPU if unavailable."""
        if self.model is not None:
            return

        if self.device == "cuda":
            try:
                logger.info("Attempting GPU initialization.")
                self.model = WhisperModel(
                    self.model_name,
                    device="cuda",
                    compute_type=STT.COMPUTE_TYPE_GPU,
                    **({"local_files_only": False} if self._hf_token else {}),
                )
                logger.info("Whisper running on GPU.")
                return
            except Exception as gpu_error:
                logger.warning(
                    f"GPU initialization failed ({gpu_error}). Falling back to CPU."
                )

        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type=STT.COMPUTE_TYPE_CPU,
        )
        logger.info("Whisper running on CPU.")

    def transcribe(self, audio_path: Path) -> str:
        """Transcribes the given audio file and returns the text."""
        if not audio_path.exists():
            raise AudioValidationError(f"Audio file not found: {audio_path}")

        if self.model is None:
            self._load_model()

        logger.info(f"Transcribing audio file: {audio_path}")
        try:
            segments, _ = self.model.transcribe(
                str(audio_path),
                beam_size=STT.BEAM_SIZE,
                language=self.language,
                task=self.task,
            )
            text = "".join(segment.text for segment in segments).strip()

            if not text:
                logger.warning("Transcription resulted in empty text.")
                return ""

            return text

        except RuntimeError as error:
            if "cuda" in str(error).lower() or "cublas" in str(error).lower() or "cudnn" in str(error).lower():
                logger.warning(
                    f"CUDA runtime error during transcription ({error}). Retrying on CPU."
                )
                self.model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type=STT.COMPUTE_TYPE_CPU,
                )
                try:
                    segments, _ = self.model.transcribe(
                        str(audio_path),
                        beam_size=STT.BEAM_SIZE,
                        language=self.language,
                        task=self.task,
                    )
                    text = "".join(segment.text for segment in segments).strip()
                    return text
                except Exception as cpu_error:
                    logger.exception("Transcription failed even on CPU.")
                    raise TranscriptionError("Failed to transcribe audio on CPU.") from cpu_error
            raise TranscriptionError("Failed to transcribe audio.") from error

        except Exception as error:
            logger.exception("Error during transcription.")
            raise TranscriptionError("Failed to transcribe audio.") from error
