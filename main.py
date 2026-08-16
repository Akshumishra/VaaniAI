import logging
from src.backend.assistant.stt.recorder import AudioRecorder
from src.backend.assistant.stt.transcriber import AudioTranscriber
from src.backend.llm.vaani_ai import VaaniAI
from src.backend.assistant.tts.speaker import TextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing components...")
    recorder = AudioRecorder()
    transcriber = AudioTranscriber()
    agent = VaaniAI()
    tts = TextToSpeech()
    
    chat_history = []
    
    print("========================================")
    print("System ready. Press Enter to start speaking (recording for 5s).")
    print("Press Ctrl+C to exit.")
    print("========================================")
    
    try:
        while True:
            input()  # Wait for user to trigger recording
            
            # 1. Record
            print("\n[Recording... Please speak]")
            audio_path = recorder.record_audio(duration_seconds=10)
            print("[Recording complete]")
            
            # 2. Transcribe
            print("[Transcribing...]")
            text = transcriber.transcribe(audio_path)
            
            if not text:
                print("No speech detected. Please try again.")
                continue
                
            print(f"\nUser: {text}")
            chat_history.append({"role": "user", "content": text})
            
            # 3. Agent Processing
            print("[VaaniAI is thinking...]")
            response_text, tool_calls = agent.invoke(chat_history)
            
            print(f"VaaniAI: {response_text}")
            chat_history.append({"role": "assistant", "content": response_text})
            
            # 4. Speak
            print("[Synthesizing speech...]")
            tts.speak(response_text)
            
            print("\nReady for next input. Press Enter to speak again.")
            
    except KeyboardInterrupt:
        print("\nExiting VaaniAI. Goodbye!")

if __name__ == "__main__":
    main()

