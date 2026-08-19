import logging
import tempfile
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from src.backend.assistant.stt.exceptions import AudioRecordingError, AudioValidationError
from src.backend.core.constants import Audio, Recording

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, sample_rate: int = Audio.SAMPLE_RATE, channels: int = Audio.CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels

    def record_audio(self, output_path: Path | None = None) -> Path:
        """Records audio until silence is detected and saves to a WAV file."""
        logger.info("Listening... (Speak now)")
        
        recorded_frames = []
        silence_frames = 0
        silence_threshold_frames = int(Recording.SILENCE_DURATION_SECONDS * self.sample_rate / Recording.CHUNK_SIZE)
        max_frames = int(Recording.MAX_DURATION_SECONDS * self.sample_rate / Recording.CHUNK_SIZE)
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate, 
                channels=self.channels, 
                dtype=np.dtype(Audio.DTYPE)
            ) as stream:
                while True:
                    data, overflowed = stream.read(Recording.CHUNK_SIZE)
                    if overflowed:
                        logger.warning("Audio buffer overflowed.")
                    
                    recorded_frames.append(data.copy())
                    
                    # Calculate volume (max amplitude in the chunk)
                    volume = np.max(np.abs(data))
                    
                    if volume < Recording.SILENCE_THRESHOLD:
                        silence_frames += 1
                    else:
                        silence_frames = 0
                        
                    # Stop if silence duration is reached and we've recorded at least a little bit
                    if silence_frames > silence_threshold_frames and len(recorded_frames) > silence_threshold_frames:
                        logger.info("Silence detected. Stopping recording.")
                        break
                        
                    if len(recorded_frames) >= max_frames:
                        logger.info("Max duration reached. Stopping recording.")
                        break
                        
        except Exception as error:
            logger.exception("Failed during audio recording.")
            raise AudioRecordingError("Failed to record audio from microphone.") from error

        # Concatenate frames to a single numpy array
        recording = np.concatenate(recorded_frames, axis=0)
        return self._save_to_wav(recording, output_path)

    def _save_to_wav(self, audio_data: np.ndarray, output_path: Path | None) -> Path:
        """Saves numpy audio data to a WAV file."""
        try:
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix=Audio.FILE_SUFFIX, delete=False)
                file_path = Path(temp_file.name)
            else:
                file_path = output_path
            
            wavfile.write(file_path, self.sample_rate, audio_data)
            logger.info(f"Audio saved to {file_path}")
            
            return file_path
        except Exception as error:
            logger.exception("Failed to save audio to WAV file.")
            raise AudioRecordingError("Failed to save recorded audio.") from error
