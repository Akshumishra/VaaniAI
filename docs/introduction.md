# Introduction

This page describes how each component of VaaniAI works internally.

## Speech-to-Text (STT)

Audio is captured in the browser using the native `MediaRecorder` API. When the user clicks the microphone button, recording begins. Clicking it again stops the recording, and the audio blob (typically `.webm` or `.ogg`, depending on the browser) is immediately sent as a file upload to the `/api/chat` endpoint.

On the server, the uploaded audio is saved to a temporary file (`generated/api_temp/user_input.wav`) and passed to the `AudioTranscriber` class. Transcription is performed via the OpenAI Audio Transcriptions API using the `whisper-1` model. The language is fixed to English (`en`). If transcription returns empty text, a system message is injected informing the LLM that no speech was detected, allowing the agent to gracefully ask the user to repeat themselves.

Relevant file: `src/backend/assistant/stt/transcriber.py`

## LLM Agent

VaaniAI uses a custom `Agent` base class (`src/backend/llm/agent_core/agent.py`) that wraps the OpenAI Chat Completions API with a tool-calling loop. The loop runs up to `max_iteration` times (default: 3). On each iteration:

1. The full conversation history is sent to the model.
2. If the model returns `tool_calls`, each tool is executed sequentially, and the result is appended back to the conversation history as a `role: tool` message.
3. This continues until the model returns a plain text response with no further tool calls.

The `VaaniAI` class (`src/backend/llm/vaani_agent/agent.py`) extends this base and is pre-configured with:

- **Model**: `gpt-4.1-mini`
- **Temperature**: `0.5`
- **System Prompt**: Instructs the agent on its role, available tools, and output format. The prompt is defined in `src/backend/llm/vaani_agent/prompt.py`.

Conversation history across turns is managed by `ConversationManager` (`src/backend/llm/agent_core/conversation.py`), which keeps the last 10 messages in memory (excluding the system prompt) to avoid exceeding token limits.

## Tools

### Web Search
The web search tool uses the Tavily Python client (`tavily-python`) to perform a `basic` depth search and return up to 3 results. Each result includes a title, URL, and a content snippet. Results are formatted as a plain-text string and returned to the agent.

Requires: `TAVILY_API_KEY` in `.env`  
Relevant file: `src/backend/llm/tools/web_search.py`

### Weather
The weather tool queries the OpenWeatherMap API (`/data/2.5/weather`) using `httpx`. It takes a location string (e.g., `"London, UK"`), fetches current conditions, and returns a formatted string including city, country, condition, temperature (Celsius), and humidity.

Requires: `WEATHERAPI_KEY` in `.env`  
Relevant file: `src/backend/llm/tools/weather.py`

### PDF Search (RAG)
The PDF search tool calls `pdf_store.search()`, which encodes the query using the same SentenceTransformer model used during ingestion, then delegates to `db_manager.search_chunks()`. Search is scoped to the currently active document by its SHA-256 hash.

Relevant files: `src/backend/llm/tools/pdf_search.py`, `src/backend/llm/rag/pdf_store.py`

## PDF Ingestion Pipeline

When a user uploads a PDF via the `/api/upload-pdf` endpoint, the following happens:

1. The file's SHA-256 hash is computed from its byte content.
2. If a document with that hash already exists in the database, processing is skipped entirely and the document is set as active immediately ("cache hit").
3. If the hash is new, the PDF is saved temporarily and processed:
   - Text is extracted page by page using `pypdf`.
   - Each page is split on double newlines (`\n\n`). If a page has fewer than two chunks and its text exceeds 1,000 characters, it is re-chunked into 500-character fixed-size segments instead.
   - Each chunk and its page number and filename are recorded as metadata.
4. All chunks are encoded in a single batch using `SentenceTransformer("all-mpnet-base-v2")` to produce 768-dimensional float vectors.
5. The chunks, metadata, embeddings, and file hash are saved to the `document_chunks` table in PostgreSQL.
6. The server streams status messages back to the frontend during processing via `StreamingResponse`.

Relevant file: `src/backend/llm/rag/pdf_store.py`

## Hybrid Search

When the agent calls `execute_pdf_search`, the system runs two parallel searches against the `document_chunks` table, filtered to the active `file_hash`:

- **Vector search**: ranks chunks by cosine distance between the query embedding and stored embeddings, retrieving the top 10.
- **Full-text search (FTS)**: uses PostgreSQL's `plainto_tsquery` and `to_tsvector` (English dictionary) to find and rank lexically matching chunks, retrieving the top 10.

The two result sets are merged using **Reciprocal Rank Fusion (RRF)** with a constant `k=60`. Each chunk receives a combined score of `1/(k + rank + 1)` from each list it appears in. The top `top_k` (default: 3) chunks by combined score are returned to the agent.

Relevant file: `src/backend/database/db_manager.py`

## Text-to-Speech (TTS)

After the agent produces its final text response, `TextToSpeech.speak()` is called. It invokes the Piper binary as a subprocess, passing the response text via stdin. Piper writes a `.wav` file to `generated/api_temp/agent_output.wav`.

The `VoiceManager` handles finding the Piper executable and voice model. If either is missing on startup, it is downloaded automatically:

- The Piper binary is downloaded from the official GitHub releases page for the detected OS (Windows, Linux, or macOS).
- The voice model (`en_US-lessac-medium`) is fetched from the `rhasspy/piper-voices` Hugging Face repository using `huggingface_hub`. An `HF_TOKEN` is required.

When `USE_BROWSER_AUDIO=True` (the default), `speak()` returns the path to the generated `.wav` file rather than playing it locally. The FastAPI endpoint then serves this file via the `/api/audio/{filename}` route, and the frontend plays it through an `<audio>` element.

Relevant files: `src/backend/assistant/tts/speaker.py`, `src/backend/assistant/tts/voice_manager.py`
