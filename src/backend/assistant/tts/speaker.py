import logging
import subprocess
import tempfile
from pathlib import Path

import sounddevice as sd
from scipy.io import wavfile

from src.backend.assistant.tts.exceptions import TextToSpeechError, AudioPlaybackError
from src.backend.assistant.tts.voice_manager import VoiceManager
from src.backend.core.constants import Audio

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Generates speech using Piper TTS and plays it through system speakers."""

    def __init__(self, voice_manager: VoiceManager | None = None):
        self.voice_manager = voice_manager or VoiceManager()

    def speak(self, text: str, voice_name: str | None = None) -> None:
        """
        Synthesizes text to speech and plays the audio.
        
        Args:
            text: The input string to convert to speech.
            voice_name: The voice model to use. Uses default if None.
            
        Raises:
            ValueError: If the text is empty or whitespace.
            TextToSpeechError: If speech generation fails.
            AudioPlaybackError: If audio playback fails.
        """
        wav_path = self.generate_audio(text, voice_name)
        try:
            self.play_audio(wav_path)
        finally:
            self._cleanup_audio(wav_path)

    def generate_audio(self, text: str, voice_name: str | None = None) -> Path:
        """
        Calls Piper TTS to generate a WAV file.
        
        Args:
            text: The input string.
            voice_name: The voice model to use.
            
        Returns:
            Path to the generated temporary WAV file.
            
        Raises:
            ValueError: If the text is empty or whitespace.
            TextToSpeechError: If generation fails.
        """
        if not text or not text.strip():
            raise ValueError("Text input cannot be empty.")

        clean_text = text.strip()
        logger.info(f"Generating speech for text: '{clean_text}'")

        piper_exe = self.voice_manager.get_piper_executable()
        model_path = self.voice_manager.get_voice_path(voice_name)
        temp_file = tempfile.NamedTemporaryFile(suffix=Audio.FILE_SUFFIX, delete=False)
        wav_path = Path(temp_file.name)
        temp_file.close()

        try:
            process = subprocess.Popen(
                [
                    str(piper_exe), 
                    "--model", str(model_path), 
                    "--output_file", str(wav_path)
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            _, stderr = process.communicate(input=clean_text)
            
            if process.returncode != 0:
                logger.error(f"Piper execution failed: {stderr}")
                raise TextToSpeechError(f"Piper TTS failed with code {process.returncode}")
                
            return wav_path
            
        except Exception as error:
            logger.exception("Failed to execute Piper TTS.")
            self._cleanup_audio(wav_path)
            raise TextToSpeechError("Audio generation failed.") from error

    def play_audio(self, audio_path: Path) -> None:
        """
        Plays a WAV file through system speakers.
        
        Args:
            audio_path: Path to the WAV file.
            
        Raises:
            AudioPlaybackError: If audio playback fails.
        """
        logger.info(f"Playing audio from {audio_path}...")
        try:
            fs, data = wavfile.read(str(audio_path))
            sd.play(data, fs)
            sd.wait()
            logger.info("Audio playback completed.")
        except Exception as error:
            logger.exception("Failed to play audio.")
            raise AudioPlaybackError("Audio playback failed.") from error

    def _cleanup_audio(self, audio_path: Path) -> None:
        """Removes the temporary audio file."""
        if audio_path.exists():
            try:
                audio_path.unlink()
                logger.debug(f"Cleaned up temp file: {audio_path}")
            except OSError as cleanup_error:
                logger.warning(f"Could not remove temp file {audio_path}: {cleanup_error}")
