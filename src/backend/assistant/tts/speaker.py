import logging
import subprocess
import tempfile
import sounddevice as sd
from scipy.io import wavfile
from pathlib import Path

from src.backend.assistant.tts.exceptions import TextToSpeechError, AudioPlaybackError
from src.backend.assistant.tts.voice_manager import VoiceManager
from src.backend.core.constants import Audio
from src.backend.core.setting import Settings

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Generates speech using Piper TTS and plays it through system speakers."""

    def __init__(self, voice_manager: VoiceManager | None = None):
        self.voice_manager = voice_manager or VoiceManager()

    def speak(
        self,
        text: str,
        voice_name: str | None = None,
        play_local: bool | None = None,
        output_path: Path | None = None,
    ) -> str | None:
        if play_local is None:
            play_local = not Settings.USE_BROWSER_AUDIO

        wav_path = self.generate_audio(text, voice_name, output_path)
        if not play_local:
            return str(wav_path)

        try:
            self.play_audio(wav_path)
        finally:
            if output_path is None:
                self._cleanup_audio(wav_path)

    def generate_audio(
        self, text: str, voice_name: str | None = None, output_path: Path | None = None
    ) -> Path:
        if not text or not text.strip():
            raise ValueError("Text input cannot be empty.")

        clean_text = text.strip()
        logger.info(f"Generating speech for text: '{clean_text}'")

        piper_exe = self.voice_manager.get_piper_executable()
        model_path = self.voice_manager.get_voice_path(voice_name)

        if output_path is not None:
            wav_path = output_path
        else:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=Audio.FILE_SUFFIX, delete=False
            )
            wav_path = Path(temp_file.name)
            temp_file.close()

        try:
            process = subprocess.Popen(
                [
                    str(piper_exe),
                    "--model",
                    str(model_path),
                    "--output_file",
                    str(wav_path),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            _, stderr = process.communicate(input=clean_text)

            if process.returncode != 0:
                logger.error(f"Piper execution failed: {stderr}")
                raise TextToSpeechError(
                    f"Piper TTS failed with code {process.returncode}"
                )

            return wav_path

        except Exception as error:
            logger.exception("Failed to execute Piper TTS.")
            if output_path is None:
                self._cleanup_audio(wav_path)
            raise TextToSpeechError("Audio generation failed.") from error

    def play_audio(self, audio_path: Path) -> None:
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
                logger.warning(
                    f"Could not remove temp file {audio_path}: {cleanup_error}"
                )
