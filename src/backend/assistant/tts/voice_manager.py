import json
import logging
import platform
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from huggingface_hub import hf_hub_download

from src.backend.assistant.tts.exceptions import VoiceNotFoundError
from src.backend.core.setting import Settings
from src.backend.core.constants import TTS, Paths, ErrorMessages

logger = logging.getLogger(__name__)


class VoiceManager:
    """Manages voice selection and Piper executable paths, downloading if missing."""

    def __init__(
        self, piper_exe_path: Path | None = None, models_dir: Path | None = None
    ):
        exe_name = "piper.exe" if platform.system() == "Windows" else "piper"

        self.piper_exe_path = piper_exe_path or (Paths.BIN_DIR / "piper" / exe_name)

        nested_path = self.piper_exe_path.parent / "piper" / exe_name
        if not self.piper_exe_path.exists() and nested_path.exists():
            self.piper_exe_path = nested_path

        self.models_dir = models_dir or (Paths.MODELS_DIR / "piper")
        self.default_voice = TTS.PIPER_DEFAULT_VOICE

    def _download_piper_binary(self) -> None:
        """Downloads the Piper binary from GitHub releases if missing."""
        if self.piper_exe_path.exists():
            return

        logger.info(f"Piper binary not found at {self.piper_exe_path}. Downloading...")

        sys_os = platform.system()
        if sys_os == "Windows":
            url = TTS.PIPER_WINDOWS_URL
        elif sys_os == "Linux":
            url = TTS.PIPER_LINUX_URL
        elif sys_os == "Darwin":
            url = TTS.PIPER_MACOS_URL
        else:
            raise VoiceNotFoundError(
                ErrorMessages.UNSUPPORTED_OS_FOR_PIPER.format(os=sys_os)
            )

        self.piper_exe_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path = self.piper_exe_path.parent / "piper_archive"

        try:
            logger.info(f"Downloading Piper from {url}...")
            urllib.request.urlretrieve(url, archive_path)

            logger.info("Extracting Piper archive...")
            if url.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(self.piper_exe_path.parent)
            else:
                with tarfile.open(archive_path, "r:gz") as tar_ref:
                    tar_ref.extractall(self.piper_exe_path.parent)

            archive_path.unlink()
            logger.info(
                f"Piper binary successfully downloaded to {self.piper_exe_path}"
            )

            if sys_os != "Windows" and self.piper_exe_path.exists():
                self.piper_exe_path.chmod(0o755)

        except Exception as error:
            logger.exception("Failed to download Piper binary.")
            raise VoiceNotFoundError(ErrorMessages.PIPER_DOWNLOAD_FAILED) from error

    def _download_voice_model(self, voice_name: str) -> None:
        """Downloads the ONNX model and config from Hugging Face using HF_TOKEN."""
        logger.info(
            f"Voice model '{voice_name}' not found locally. Fetching from Hugging Face..."
        )
        self.models_dir.mkdir(parents=True, exist_ok=True)

        repo_id = TTS.PIPER_REPO_ID
        token = Settings.HF_TOKEN

        try:
            voices_json_path = hf_hub_download(
                repo_id=repo_id, filename=TTS.PIPER_VOICES_JSON_FILENAME, token=token
            )
            with open(voices_json_path, "r", encoding="utf-8") as f:
                voices_data = json.load(f)

            if voice_name not in voices_data:
                raise VoiceNotFoundError(
                    ErrorMessages.VOICE_NOT_IN_REGISTRY.format(voice_name=voice_name)
                )

            voice_info = voices_data[voice_name]
            files_to_download = list(voice_info.get("files", {}).keys())

            target_files = [
                f
                for f in files_to_download
                if f.endswith(".onnx") or f.endswith(".json")
            ]

            for file_path in target_files:
                logger.info(f"Downloading {file_path}...")
                cached_file = hf_hub_download(
                    repo_id=repo_id, filename=file_path, token=token
                )
                dest_file = self.models_dir / Path(file_path).name
                shutil.copy2(cached_file, dest_file)
                logger.debug(f"Copied to {dest_file}")

            logger.info(f"Voice '{voice_name}' successfully downloaded and cached.")

        except Exception as error:
            logger.exception(
                f"Failed to download voice model '{voice_name}' from Hugging Face."
            )
            raise VoiceNotFoundError(
                ErrorMessages.VOICE_DOWNLOAD_FAILED.format(voice_name=voice_name)
            ) from error

    def get_piper_executable(self) -> Path:
        """
        Returns the configured path to the Piper binary.
        Downloads it if it doesn't exist.
        """
        self._download_piper_binary()

        if not self.piper_exe_path.exists():
            nested_path = (
                self.piper_exe_path.parent / "piper" / self.piper_exe_path.name
            )
            if nested_path.exists():
                self.piper_exe_path = nested_path
            else:
                raise VoiceNotFoundError(
                    ErrorMessages.PIPER_NOT_FOUND_AFTER_DOWNLOAD.format(path=self.piper_exe_path)
                )

        return self.piper_exe_path

    def get_voice_path(self, voice_name: str | None = None) -> Path:
        """
        Returns the path to the .onnx model for the selected voice.
        Downloads it via Hugging Face if not found locally.
        """
        target_voice = voice_name or self.default_voice
        model_path = self.models_dir / f"{target_voice}.onnx"
        config_path = self.models_dir / f"{target_voice}.onnx.json"

        if not model_path.exists() or not config_path.exists():
            self._download_voice_model(target_voice)

        if not model_path.exists():
            raise VoiceNotFoundError(ErrorMessages.VOICE_MODEL_MISSING_AFTER_DOWNLOAD.format(path=model_path))

        return model_path
