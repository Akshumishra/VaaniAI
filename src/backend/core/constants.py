from pathlib import Path

class Paths:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    LOGS_DIR = BASE_DIR / "logs"
    GENERATED_DIR = BASE_DIR / "generated"
    MODELS_DIR = BASE_DIR / "models"
    BIN_DIR = BASE_DIR / "bin"
    ENV_PATH = SRC_DIR / ".env"
    AUDIO_FILENAME = "audio.wav"

class Audio:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "int16"
    FILE_SUFFIX = ".wav"

class STT:
    MODEL_NAME = "base"
    LANGUAGE = "en"
    TASK = "transcribe"
    DEVICE = "cuda"
    COMPUTE_TYPE_GPU = "float16"
    COMPUTE_TYPE_CPU = "int8"
    BEAM_SIZE = 5

class Recording:
    DEFAULT_DURATION_SECONDS = 5

class TTS:
    PIPER_DEFAULT_VOICE = "en_US-lessac-medium"
    PIPER_REPO_ID = "rhasspy/piper-voices"
    PIPER_VOICES_JSON_FILENAME = "voices.json"

    PIPER_WINDOWS_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
    PIPER_LINUX_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
    PIPER_MACOS_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_macos_aarch64.tar.gz"
