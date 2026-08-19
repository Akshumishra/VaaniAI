import sys

from src.backend.assistant.stt.recorder import AudioRecorder
from src.backend.assistant.stt.transcriber import AudioTranscriber
from src.backend.core.logger import setup_logging
from src.backend.core.constants import STT, Paths, Recording


def main():
    setup_logging()
    
    recorder = AudioRecorder()
    transcriber = AudioTranscriber(model_name=STT.MODEL_NAME)
    
    Paths.GENERATED_DIR.mkdir(exist_ok=True)
    audio_file_path = Paths.GENERATED_DIR / Paths.AUDIO_FILENAME
    
    print("Recording...")
    try:
        saved_path = recorder.record_audio(
            duration_seconds=Recording.DEFAULT_DURATION_SECONDS,
            output_path=audio_file_path
        )
        print("Recording complete.")
        
        print("Transcribing...")
        text = transcriber.transcribe(saved_path)
        
        print("Transcription:")
        print(text)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
