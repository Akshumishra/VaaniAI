from pathlib import Path


class Logs:
    logs_dir = Path("logs")
    level = "INFO"


class Audio:
    sample_rate = 16000
    channels = 1
    dtype = "int16"
    file_suffix = ".wav"


class STT:
    model_name = "base"
    language = "en"
    task = "transcribe"
    device = "cuda"
    compute_type_gpu = "float16"
    compute_type_cpu = "int8"
    beam_size = 5
    hf_token_env_key = "HF_TOKEN"


class Paths:
    generated_dir = Path("generated")
    audio_filename = "audio.wav"


class Recording:
    default_duration_seconds = 5