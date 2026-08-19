# Local Setup

## Prerequisites

- Python 3.14 or newer
- PostgreSQL with the `pgvector` extension installed
- A Hugging Face account (needed to download the Piper TTS voice model on first run)

## Steps

### 1. Clone the repository

```bash
git clone https://github.com/Akshumishra/VaaniAI.git
cd VaaniAI
```

### 2. Install dependencies with `uv`

`uv` will create a `.venv` virtual environment and install all packages from `pyproject.toml`.

```bash
uv sync
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Configure environment variables

Copy `.env.sample` to `.env` and fill in your values:

```bash
cp .env.sample .env
```

Open `.env` and set the following:

```env
HF_TOKEN=your_hugging_face_access_token
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
WEATHERAPI_KEY=your_weatherapi_key
LOG_LEVEL=INFO
USE_BROWSER_AUDIO=True
```

**Variable notes:**

- `OPENAI_API_KEY` — used for both speech transcription (Whisper) and LLM reasoning. Required.
- `DATABASE_URL` — defaults to `postgresql://postgres:postgres@localhost:5432/postgres`. Override if your PostgreSQL setup differs.
- `HF_TOKEN` — required only for the first run to download the Piper voice model from Hugging Face. After the model is cached locally under `models/piper/`, it is no longer needed at runtime.
- `TAVILY_API_KEY` — required only if you want the web search tool to function.
- `WEATHERAPI_KEY` — this is an OpenWeatherMap API key, required only if you want the weather tool to function.
- `USE_BROWSER_AUDIO` — set to `True` (the default) when using the web UI. Set to `False` only if running without a browser and you want audio played through local system speakers.

### 4. Set up the database

Ensure PostgreSQL is running and the `pgvector` extension is available. The application will create the `document_chunks` table automatically on first startup via SQLAlchemy.

To install `pgvector` on your PostgreSQL instance (if not already done):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Run the application

Start the FastAPI server:

```bash
uvicorn src.backend.api.main:app --reload
```

Open your browser and navigate to:

```
http://localhost:8000
```

The first time the server starts, it will download the Piper binary and the `en_US-lessac-medium` voice model if they are not already present in `bin/` and `models/piper/`. This may take a minute depending on your connection speed.

## Running the Documentation Site

To preview this documentation locally:

```bash
uv run mkdocs serve
```

Navigate to `http://127.0.0.1:8000` (or `http://127.0.0.1:8001` if the app server is already running on port 8000).
