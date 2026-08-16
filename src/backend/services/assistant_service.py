import logging
from src.backend.assistant.stt.recorder import AudioRecorder
from src.backend.assistant.stt.transcriber import AudioTranscriber
from src.backend.llm.providers.openai_provider import OpenAIProvider
from src.backend.llm.agent_core.conversation import ConversationManager
from src.backend.assistant.tts.speaker import TextToSpeech
from src.backend.core.constants import Paths
from src.backend.llm.tools.web_search import WEB_SEARCH_SCHEMA, execute_web_search
from src.backend.llm.tools.weather import WEATHER_SCHEMA, execute_weather_check

logger = logging.getLogger(__name__)

class VoiceAssistant:
    """The central service that orchestrates STT, LLM, and TTS modules."""

    def __init__(self):
        logger.info("Initializing Voice Assistant components...")
        self.recorder = AudioRecorder()
        self.transcriber = AudioTranscriber()
        self.llm_provider = OpenAIProvider()
        self.conversation = ConversationManager()
        self.tts = TextToSpeech()
        
        Paths.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        self.audio_filepath = Paths.GENERATED_DIR / Paths.AUDIO_FILENAME
        
        logger.info("Voice Assistant ready.")

    def process_turn(self):
        """Executes a single turn of the voice assistant interaction."""
        try:
            # 1. Record Audio (will stop automatically on silence)
            audio_path = self.recorder.record_audio(output_path=self.audio_filepath)
            
            # 2. Transcribe Audio
            text = self.transcriber.transcribe(audio_path)
            
            if not text:
                logger.info("No speech detected. Skipping turn.")
                return
                
            print(f"\nUser: {text}")
            
            # Exit command logic (optional, for convenience)
            if text.lower().strip() in ["goodbye", "exit", "stop", "quit"]:
                print("VaaniAI: Goodbye!")
                self.tts.speak("Goodbye!")
                raise KeyboardInterrupt
            
            # 3. LLM Response
            self.conversation.add_user_message(text)
            
            response = self.llm_provider.generate_response(
                self.conversation.get_messages(),
                tools=[WEB_SEARCH_SCHEMA, WEATHER_SCHEMA],
                tool_map={
                    "web_search": execute_web_search,
                    "get_current_weather": execute_weather_check
                }
            )
            
            self.conversation.add_assistant_message(response)
            
            print(f"VaaniAI: {response}\n")
            
            # 4. Text-to-Speech
            self.tts.speak(response)
            
        except Exception as e:
            logger.error(f"Error during interaction turn: {e}")

    def run_continuous_loop(self):
        """Runs the assistant in a continuous listening loop."""
        print("\n--- VaaniAI Continuous Loop Started ---")
        print("Speak into your microphone. Say 'goodbye' to stop.\n")
        try:
            while True:
                self.process_turn()
        except KeyboardInterrupt:
            print("\nExiting VaaniAI.")
            logger.info("Continuous loop stopped by user.")
