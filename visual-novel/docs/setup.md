# Japanese Learning Visual Novel - Setup Guide

This guide will walk you through the process of setting up and running the Japanese Learning Visual Novel application.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Docker and Docker Compose**
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

2. **Ren'Py SDK** (for development)
   - [Ren'Py Download Page](https://www.renpy.org/latest.html)
   - Version 7.4.0 or higher recommended

3. **Python 3.8+** (for development and testing)
   - [Python Download Page](https://www.python.org/downloads/)

## Installation Steps

### Step 1: Initial Setup (Run Once)

The visual novel requires two sets of services:
1. **opea-docker services** (LLM, TTS, ASR, image generation, etc.)
2. **visual novel services** (game server, web server)

**Option A: Use the main launcher (Recommended)**
```bash
# From the project root directory
python first_start.py  # Creates virtual environments and starts opea-docker services (including Visual Novel)
python project_start.py  # Launches the visual novel (services already running)
```

**Option B: Manual setup**
```bash
# 1. Create virtual environments and start opea-docker services (includes Visual Novel)
python first_start.py

# 2. Visual Novel services are now automatically included in opea-docker
# No additional setup needed!
```

### Step 2: Configure Environment Variables

The `.env` file in the visual-novel directory is automatically configured with the correct service endpoints. The file includes:

```
# Flask settings
SECRET_KEY=your-secret-key
FLASK_DEBUG=true

# Database
DATABASE_URL=sqlite:///../data/shared_db/visual_novel.db

# Service endpoints for opea-docker containers
OLLAMA_SERVER_URL=http://ollama-server:11434
LLM_TEXT_URL=http://ollama-server:11434
GUARDRAILS_URL=http://guardrails:9400
CHROMADB_URL=http://chromadb:8000
TTS_URL=http://tts:9200
ASR_URL=http://asr:9300
LLM_VISION_URL=http://llm-vision:9101
WAIFU_DIFFUSION_URL=http://waifu-diffusion:9500
EMBEDDINGS_URL=http://embeddings:6000

# Ollama configuration
OLLAMA_URL=http://ollama-server:11434
OLLAMA_MODEL=llama3.2

# Application settings
PORT=8080
USE_REMOTE_DB=true
```

### Step 3: Verify Services

Check that all services are running correctly:

```bash
# Check all services including Visual Novel
cd opea-docker
docker compose ps
```

You should see all services in the "Up" state, including:
- ollama-server
- chromadb
- tts
- asr
- llm-vision
- mangaocr
- waifu-diffusion
- guardrails
- embeddings
- vn-game-server
- vn-web-server

Test the API Gateway:

```bash
curl http://localhost:8080/api/health
```

You should receive a response like: `{"status":"ok"}`

### Step 4: Running the Visual Novel

#### Web Version

Access the web version of the visual novel by opening a browser and navigating to:

```
http://localhost:8001
```

#### Desktop Version (Development)

To run the desktop version using the Ren'Py SDK:

1. Open the Ren'Py launcher
2. Click "Add Existing Project"
3. Navigate to the `visual-novel/renpy` directory and select it
4. Select the project from the list and click "Launch Project"

#### Local Development Server

To run the server locally for development:

```bash
cd visual-novel/server
source .venv-vn/bin/activate
python app.py
```

## Service Architecture

The visual novel uses a microservices architecture:

### opea-docker Services (Required)
- **ollama-server**: LLM for text generation and conversations
- **tts**: Text-to-speech for Japanese audio
- **asr**: Speech recognition for voice input
- **llm-vision**: Image understanding and description
- **waifu-diffusion**: Anime-style image generation
- **guardrails**: Content filtering and safety
- **embeddings**: Vector embeddings for semantic search
- **chromadb**: Vector database for embeddings

### Visual Novel Services
- **vn-game-server**: Game server and API gateway (port 8080)
- **vn-web-server**: Web server for Ren'Py web export (port 8001)

## Configuration Options

### Database Configuration

By default, the application uses SQLite for data storage. The database file is located at:

```
data/shared_db/visual_novel.db
```

in the project root directory, which is shared between all services and mapped to `/app/db/visual_novel.db` inside the Docker container.

### API Services Configuration

The application communicates with various AI services through the opea-docker containers. All service endpoints are configured in the `.env` file and automatically passed to the Docker containers.

## Troubleshooting

### Docker Services Not Starting

If any of the Docker services fail to start, check the logs:

```bash
# Check all services including Visual Novel
cd opea-docker
docker compose logs
```

Common issues include:
- Port conflicts: Change the port mappings in `docker-compose.yml`
- Missing environment variables: Ensure all required environment variables are set
- Network issues: Ensure the opea-docker network exists and is accessible

### Web Version Not Loading

If the web version doesn't load correctly:

1. Check that the web server is running: `docker compose ps vn-web-server`
2. Verify that the Ren'Py web export files exist in `visual-novel/renpy/web`
3. Check the web server logs: `docker compose logs vn-web-server`

### API Communication Issues

If the visual novel can't communicate with the API services:

1. Ensure the game server is running: `docker compose ps vn-game-server`
2. Check the game server logs: `docker compose logs vn-game-server`
3. Verify that the opea-docker services are accessible from the game server container

### Virtual Environment Issues

If you encounter virtual environment issues:

1. Ensure the virtual environment exists: `ls -la visual-novel/server/.venv-vn`
2. Recreate the virtual environment: `python first_start.py`
3. Check Python dependencies: `cd visual-novel/server && source .venv-vn/bin/activate && pip list`

## Next Steps

After successful setup, refer to the [Development Guide](development.md) for information on extending and customizing the visual novel.