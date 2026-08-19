import os
import shutil
import logging
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from src.backend.assistant.stt.transcriber import AudioTranscriber
from src.backend.assistant.tts.speaker import TextToSpeech
from src.backend.llm.vaani_agent.agent import VaaniAI
from src.backend.llm.agent_core.conversation import ConversationManager
from src.backend.llm.tools.web_search import web_search_tool
from src.backend.llm.tools.weather import weather_tool
from src.backend.llm.tools.pdf_search import pdf_search_tool
from src.backend.llm.rag.pdf_store import pdf_store
from src.backend.core.constants import Paths
from src.backend.core.setting import Settings

logging.basicConfig(
    level=getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VaaniAI API")

transcriber = AudioTranscriber()
agent = VaaniAI()
agent.add_tool(web_search_tool)
agent.add_tool(weather_tool)
agent.add_tool(pdf_search_tool)
conversation = ConversationManager()
tts = TextToSpeech()

TEMP_DIR = Path(Paths.GENERATED_DIR) / "api_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/api/chat")
async def chat_endpoint(audio: UploadFile = File(...)):
    """Receives audio from browser, processes it, and returns TTS audio."""
    temp_input_path = TEMP_DIR / "user_input.wav"

    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        logger.info("Transcribing uploaded audio...")
        text = transcriber.transcribe(temp_input_path)

        if not text:
            logger.info("No speech detected. Informing LLM.")
            text = "[System: The user submitted an audio clip, but no speech was detected. Please politely ask them to repeat themselves or check their microphone.]"

        logger.info(f"User said: {text}")
        conversation.add_user_message(text)

        response_text, _ = agent.invoke(conversation.get_messages())
        conversation.add_assistant_message(response_text)
        logger.info(f"VaaniAI response: {response_text}")

        logger.info("Generating TTS audio...")
        temp_output_path = TEMP_DIR / "agent_output.wav"
        audio_out_path = tts.speak(response_text, output_path=temp_output_path)
        filename = Path(audio_out_path).name
        return {
            "user_text": text,
            "assistant_text": response_text,
            "audio_url": f"/api/audio/{filename}",
        }
    except Exception as e:
        logger.exception("Error processing chat.")
        return {"error": str(e)}


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Serves the generated TTS audio file."""
    file_path = TEMP_DIR / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/wav")
    return {"error": "Audio file not found."}


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Receives a PDF and streams its processing status back to the frontend."""
    import hashlib

    sha256_hash = hashlib.sha256()
    content = await file.read()
    sha256_hash.update(content)
    file_hash = sha256_hash.hexdigest()

    temp_pdf_path = TEMP_DIR / f"{file_hash}.pdf"

    with open(temp_pdf_path, "wb") as buffer:
        buffer.write(content)

    return StreamingResponse(
        pdf_store.add_pdf_generator(str(temp_pdf_path), file_hash, file.filename),
        media_type="text/plain",
    )


frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
