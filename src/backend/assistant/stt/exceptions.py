class STTBaseError(Exception):
    """Base exception for all STT errors."""

    pass


class AudioRecordingError(STTBaseError):
    """Raised when audio recording fails."""

    pass


class AudioValidationError(STTBaseError):
    """Raised when audio validation fails."""

    pass


class TranscriptionError(STTBaseError):
    """Raised when transcription fails."""

    pass
