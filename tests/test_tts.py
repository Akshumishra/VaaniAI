import sys
from pathlib import Path

# Add project root to sys.path so that 'src' is resolvable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.backend.core.logger import setup_logging
from src.backend.assistant.tts.speaker import TextToSpeech
from src.backend.assistant.tts.exceptions import TextToSpeechError


def main():
    setup_logging()

    print("Initializing TTS...")
    try:
        tts = TextToSpeech()

        # Verify voice exists by requesting the path first
        tts.voice_manager.get_piper_executable()
        tts.voice_manager.get_voice_path()
        print("Voice loaded.")

        text = "Hello Akshita, welcome to Vaani AI. How can i help you?"

        print("Generating speech...")
        audio_path = tts.generate_audio(text)

        print("Playing audio...")
        tts.play_audio(audio_path)

        # Cleanup happens manually since we bypassed tts.speak() to print between steps
        tts._cleanup_audio(audio_path)

        print("Done.")

    except TextToSpeechError as e:
        print(f"TTS Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
