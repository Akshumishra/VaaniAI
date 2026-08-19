from pathlib import Path


class Paths:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    LOGS_DIR = BASE_DIR / "logs"
    GENERATED_DIR = BASE_DIR / "generated"
    MODELS_DIR = BASE_DIR / "models"
    BIN_DIR = BASE_DIR / "bin"
    ENV_PATH = BASE_DIR / ".env"
    AUDIO_FILENAME = "audio.wav"


class Audio:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "int16"
    FILE_SUFFIX = ".wav"


class STT:
    MODEL_NAME = "whisper-1"
    LANGUAGE = "en"


class Recording:
    MAX_DURATION_SECONDS = 30
    SILENCE_THRESHOLD = 500
    SILENCE_DURATION_SECONDS = 1.5
    CHUNK_SIZE = 1024


class TTS:
    PIPER_DEFAULT_VOICE = "en_US-lessac-medium"
    PIPER_REPO_ID = "rhasspy/piper-voices"
    PIPER_VOICES_JSON_FILENAME = "voices.json"

    PIPER_WINDOWS_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
    PIPER_LINUX_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
    PIPER_MACOS_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_macos_aarch64.tar.gz"


class LLM:
    DEFAULT_MODEL = "gpt-4.1-mini"
    MAX_TOKENS = 200
    TEMPERATURE = None

class ErrorMessages:
    # --- Generic ---
    GENERIC = "Something went wrong. Please try again."
    UNEXPECTED = "Unexpected error: {e}"

    # --- API / OpenAI ---
    MISSING_OPENAI_API_KEY = "OPENAI_API_KEY is required but was not provided."
    NO_LLM_CHOICES = "No choices returned from OpenAI API."
    API_CONNECTION_FAILED = "Failed to connect to OpenAI API: {e}"
    API_GENERATION_FAILED = "OpenAI API failed to generate a response: {e}"

    # --- Tool execution ---
    TOOL_EXECUTION_FAILED = "Error executing tool: {e}"
    TOOL_NOT_FOUND = "Tool '{func_name}' not found."

    # --- STT ---
    AUDIO_FILE_NOT_FOUND = "Audio file not found: {path}"
    TRANSCRIPTION_FAILED = "Failed to transcribe audio via OpenAI."
    EMPTY_TEXT_INPUT = "Text input cannot be empty."

    # --- TTS / Voice Manager ---
    PIPER_DOWNLOAD_FAILED = "Could not download Piper binary."
    PIPER_NOT_FOUND_AFTER_DOWNLOAD = "Piper executable still not found after download at {path}"
    UNSUPPORTED_OS_FOR_PIPER = "Unsupported OS for automatic Piper download: {os}"
    VOICE_NOT_IN_REGISTRY = "Voice '{voice_name}' not found in the Piper voices registry."
    VOICE_DOWNLOAD_FAILED = "Could not download voice '{voice_name}'."
    VOICE_MODEL_MISSING_AFTER_DOWNLOAD = "Model path missing after download: {path}"
    PIPER_EXECUTION_FAILED = "Piper TTS failed with code {code}"
    AUDIO_GENERATION_FAILED = "Audio generation failed."
    AUDIO_PLAYBACK_FAILED = "Audio playback failed."

    # --- API endpoints ---
    AUDIO_FILE_NOT_FOUND_ENDPOINT = "Audio file not found."

    # --- Empty speech ---
    NO_SPEECH_DETECTED = (
        "[System: The user submitted an audio clip, but no speech was detected. "
        "Please politely ask them to repeat themselves or check their microphone.]"
    )
