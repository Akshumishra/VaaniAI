# Technical Design

## System Architecture

The diagram below shows the high-level component layout of VaaniAI.

```mermaid
graph TD
    Browser["Browser (Frontend)"]

    subgraph FastAPI Backend
        API["API Layer\n(src/backend/api/main.py)"]
        STT["AudioTranscriber\n(OpenAI Whisper API)"]
        Agent["VaaniAI Agent\n(gpt-4.1-mini)"]
        TTS["TextToSpeech\n(Piper TTS)"]
        ConvMgr["ConversationManager"]

        subgraph Tools
            WebSearch["Web Search\n(Tavily)"]
            Weather["Weather\n(OpenWeatherMap)"]
            PDFSearch["PDF Search\n(RAG)"]
        end

        subgraph RAG Pipeline
            PDFStore["PDFStore\n(SentenceTransformer)"]
            DBMgr["DatabaseManager\n(Hybrid Search)"]
        end
    end

    PostgreSQL[("PostgreSQL\n+ pgvector\ndocument_chunks")]

    Browser -- "POST /api/chat (audio)" --> API
    Browser -- "POST /api/upload-pdf (pdf)" --> API
    API --> STT
    STT --> Agent
    Agent --> ConvMgr
    Agent --> WebSearch
    Agent --> Weather
    Agent --> PDFSearch
    PDFSearch --> PDFStore
    PDFStore --> DBMgr
    API --> PDFStore
    DBMgr <--> PostgreSQL
    Agent --> TTS
    TTS -- "GET /api/audio/..." --> Browser
```

## Project Structure

```
VaaniAI/
├── src/
│   ├── backend/
│   │   ├── api/
│   │   │   └── main.py              # FastAPI application, all HTTP endpoints
│   │   ├── assistant/
│   │   │   ├── stt/
│   │   │   │   ├── transcriber.py   # OpenAI Whisper transcription
│   │   │   │   └── exceptions.py    # TranscriptionError, AudioValidationError
│   │   │   └── tts/
│   │   │       ├── speaker.py       # Piper TTS subprocess wrapper (browser-only output)
│   │   │       ├── voice_manager.py # Piper binary and voice model management
│   │   │       └── exceptions.py    # TextToSpeechError, VoiceNotFoundError
│   │   ├── core/
│   │   │   ├── constants.py         # All app constants + ErrorMessages (single source of truth)
│   │   │   ├── setting.py           # Environment variable loader (Settings class)
│   │   │   └── logger.py
│   │   ├── database/
│   │   │   ├── models.py            # SQLAlchemy ORM model (DocumentChunk)
│   │   │   └── db_manager.py        # DB init, save, and hybrid search logic
│   │   └── llm/
│   │       ├── agent_core/
│   │       │   ├── agent.py         # Base Agent class with tool-calling loop
│   │       │   ├── conversation.py  # ConversationManager (history + trimming)
│   │       │   ├── tools.py         # Tool wrapper class
│   │       │   ├── arg_schema.py    # Tool argument schema builder
│   │       │   └── constants.py     # Agent defaults (model, temperature, iterations)
│   │       ├── vaani_agent/
│   │       │   ├── agent.py         # VaaniAI subclass (pre-configured agent)
│   │       │   ├── prompt.py        # VaaniAI system prompt
│   │       │   └── constant.py      # VaaniAI model, temperature, iteration config
│   │       ├── providers/
│   │       │   └── openai_provider.py
│   │       ├── rag/
│   │       │   └── pdf_store.py     # PDF chunking, embedding, and search
│   │       └── tools/
│   │           ├── web_search.py
│   │           ├── weather.py
│   │           └── pdf_search.py
│   └── frontend/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── docs/                            # MkDocs documentation source
├── tests/
├── pyproject.toml
└── mkdocs.yml
```

## API Endpoints

The FastAPI application is defined in `src/backend/api/main.py`. It exposes three endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Receives a `.wav` audio upload, transcribes it, runs the agent, returns text and audio URL |
| `GET` | `/api/audio/{filename}` | Serves the generated TTS `.wav` file to the browser |
| `POST` | `/api/upload-pdf` | Receives a PDF, computes its hash, ingests it if new, streams status text back |

The frontend HTML/JS/CSS is served under `/` via FastAPI's `StaticFiles` mount.

## Data Flow

### Voice Chat Turn

```mermaid
sequenceDiagram
    participant Browser
    participant API as FastAPI API
    participant STT as AudioTranscriber
    participant LLM as VaaniAI Agent
    participant Tool as Tool (optional)
    participant TTS as TextToSpeech

    Browser->>API: POST /api/chat (audio blob)
    API->>API: Save to user_input.wav
    API->>STT: transcribe(audio_path)
    STT->>STT: OpenAI Whisper API call
    STT-->>API: Transcribed text

    API->>LLM: invoke(conversation_history)
    loop Agent loop (max 3 iterations)
        LLM->>LLM: Call OpenAI gpt-4.1-mini
        alt Tool call requested
            LLM->>Tool: execute tool (web_search / weather / pdf_search)
            Tool-->>LLM: Tool result appended to history
        else Plain text response
            LLM-->>API: Final response text
        end
    end

    API->>TTS: speak(response_text, output_path)
    TTS->>TTS: Run Piper subprocess
    TTS-->>API: Path to agent_output.wav

    API-->>Browser: { user_text, assistant_text, audio_url }
    Browser->>API: GET /api/audio/agent_output.wav
    API-->>Browser: WAV file
    Browser->>Browser: Play audio via HTML5 Audio API
```

### PDF Upload and Ingestion

```mermaid
sequenceDiagram
    participant Browser
    participant API as FastAPI API
    participant PDFStore
    participant DB as DatabaseManager
    participant PG as PostgreSQL

    Browser->>API: POST /api/upload-pdf (pdf file)
    API->>API: Compute SHA-256 hash

    API->>DB: check_document_exists(hash)
    DB->>PG: Query document_chunks WHERE file_hash = hash
    PG-->>DB: Result

    alt Hash already exists (cache hit)
        DB-->>API: True
        API->>PDFStore: Set active_file_hash
        API-->>Browser: Stream "Document already processed. Ready."
    else New document
        DB-->>API: False
        API->>PDFStore: add_pdf_generator(path, hash, filename)
        PDFStore-->>Browser: Stream "Extracting text..."
        PDFStore->>PDFStore: pypdf extracts text per page
        PDFStore->>PDFStore: Chunk text (newline split or 500-char fixed)
        PDFStore-->>Browser: Stream "Generating embeddings..."
        PDFStore->>PDFStore: SentenceTransformer encodes all chunks
        PDFStore->>DB: save_chunks(metadata, chunks, embeddings, hash)
        DB->>PG: INSERT INTO document_chunks
        PG-->>DB: OK
        PDFStore-->>Browser: Stream "Ready."
    end
```

## Agent Tool-Calling Loop

```mermaid
flowchart TD
    Start([User message received]) --> AddHistory[Add to ConversationManager]
    AddHistory --> CallLLM["Call OpenAI gpt-4.1-mini\nwith full history + system prompt"]
    CallLLM --> HasToolCalls{Tool calls\nin response?}

    HasToolCalls -- Yes --> ExecTool[Execute each tool\nin order]
    ExecTool --> AppendResult[Append tool results\nto history as role:tool]
    AppendResult --> CheckIter{Max iterations\nreached?}
    CheckIter -- No --> CallLLM
    CheckIter -- Yes --> Error([Return error message])

    HasToolCalls -- No --> FinalResponse[Return plain text response]
    FinalResponse --> AddAssistant[Add to conversation history]
    AddAssistant --> TTS([Pass to TextToSpeech])
```

## Error Handling

All error messages are centralized in the `ErrorMessages` class inside `src/backend/core/constants.py`. This is the single source of truth for every exception string raised across the backend — no hardcoded strings in individual modules.

```mermaid
graph LR
    A["ErrorMessages\nsrc/backend/core/constants.py"]
    A --> B["openai_provider.py"]
    A --> C["transcriber.py"]
    A --> D["speaker.py"]
    A --> E["voice_manager.py"]
    A --> F["main.py"]
```

### Error Categories

| Category | Constants |
|---|---|
| Generic | `GENERIC`, `UNEXPECTED` |
| API / OpenAI | `MISSING_OPENAI_API_KEY`, `NO_LLM_CHOICES`, `API_CONNECTION_FAILED`, `API_GENERATION_FAILED` |
| Tool Execution | `TOOL_EXECUTION_FAILED`, `TOOL_NOT_FOUND` |
| STT | `AUDIO_FILE_NOT_FOUND`, `TRANSCRIPTION_FAILED`, `EMPTY_TEXT_INPUT` |
| TTS / Voice | `PIPER_DOWNLOAD_FAILED`, `PIPER_NOT_FOUND_AFTER_DOWNLOAD`, `UNSUPPORTED_OS_FOR_PIPER`, `VOICE_NOT_IN_REGISTRY`, `VOICE_DOWNLOAD_FAILED`, `VOICE_MODEL_MISSING_AFTER_DOWNLOAD`, `PIPER_EXECUTION_FAILED`, `AUDIO_GENERATION_FAILED` |
| API Endpoints | `AUDIO_FILE_NOT_FOUND_ENDPOINT`, `NO_SPEECH_DETECTED` |

## Database Schema

VaaniAI uses a single PostgreSQL table for RAG storage.

### Entity Relationship Diagram

```mermaid
erDiagram
    DOCUMENT_CHUNKS {
        integer id PK
        text document_name
        text file_hash
        integer page_number
        text chunk_text
        vector_768 embedding
    }
```

**Notes:**

- `file_hash` stores the SHA-256 hex digest of the original PDF file's byte content. It is indexed for fast lookups and scopes all search queries to a single document.
- `embedding` is a 768-dimensional float vector produced by the `all-mpnet-base-v2` SentenceTransformer model, stored via the `pgvector` extension (`Vector(768)`).
- There are no foreign keys. Each row is a self-contained chunk. Documents are identified logically by `file_hash`, and only one document (the most recently uploaded) is treated as "active" per server session.

## Configuration

All configuration is loaded from environment variables via `Settings` in `src/backend/core/setting.py`. The `.env` file is loaded automatically from the project root.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | Used for Whisper transcription and LLM calls |
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@localhost:5432/postgres` | PostgreSQL connection string |
| `HF_TOKEN` | Yes (first run) | — | Hugging Face token for downloading the Piper voice model |
| `TAVILY_API_KEY` | Optional | — | Required for the web search tool |
| `WEATHERAPI_KEY` | Optional | — | Required for the weather tool (OpenWeatherMap key) |
| `LOG_LEVEL` | Optional | `INFO` | Python logging level |
| `USE_BROWSER_AUDIO` | Optional | `True` | TTS audio is always served over HTTP to the browser. Local system audio playback has been removed. |

## Technology Stack

| Component | Library / Service |
|-----------|-------------------|
| Web framework | FastAPI + Uvicorn |
| Speech-to-text | OpenAI Whisper API (`whisper-1`) |
| LLM | OpenAI Chat Completions API (`gpt-4.1-mini`) |
| Text-to-speech | Piper TTS (`en_US-lessac-medium` ONNX model) |
| Embeddings | `sentence-transformers` (`all-mpnet-base-v2`) |
| Vector database | PostgreSQL + `pgvector` |
| ORM | SQLAlchemy |
| PDF parsing | `pypdf` |
| Web search | Tavily API (`tavily-python`) |
| Weather | OpenWeatherMap API (`httpx`) |
| Frontend | HTML / Vanilla JS / CSS |
| Dependency management | `uv` |
