import logging
import tempfile
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from src.backend.assistant.stt.exceptions import AudioRecordingError, AudioValidationError
from src.backend.core.constants import Audio

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, sample_rate: int = Audio.sample_rate, channels: int = Audio.channels):
        self.sample_rate = sample_rate
        self.channels = channels

    def record_audio(self, duration_seconds: int, output_path: Path | None = None) -> Path:
        """Records audio for a given duration and saves to a WAV file."""
        if duration_seconds <= 0:
            raise AudioValidationError(f"Invalid duration: {duration_seconds}s. Must be > 0.")

        logger.info(f"Starting recording for {duration_seconds} seconds...")
        
        try:
            recording = sd.rec(
                int(duration_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.dtype(Audio.dtype)
            )
            sd.wait()
            logger.info("Recording completed.")
        except Exception as error:
            logger.exception("Failed during audio recording.")
            raise AudioRecordingError("Failed to record audio from microphone.") from error

        return self._save_to_wav(recording, output_path)

    def _save_to_wav(self, audio_data: np.ndarray, output_path: Path | None) -> Path:
        """Saves numpy audio data to a WAV file."""
        try:
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix=Audio.file_suffix, delete=False)
                file_path = Path(temp_file.name)
            else:
                file_path = output_path
            
            wavfile.write(file_path, self.sample_rate, audio_data)
            logger.info(f"Audio saved to {file_path}")
            
            return file_path
        except Exception as error:
            logger.exception("Failed to save audio to WAV file.")
            raise AudioRecordingError("Failed to save recorded audio.") from error
