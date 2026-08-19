class TextToSpeechError(Exception):
    """Base exception for all TTS errors."""

    pass


class VoiceNotFoundError(TextToSpeechError):
    """Raised when the specified voice model is not found."""

    pass
