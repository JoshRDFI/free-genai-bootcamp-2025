# Development Guide for Japanese Learning Visual Novel

## Project Architecture

The Japanese Learning Visual Novel is built with a client-server architecture:

- **Client**: Ren'Py visual novel engine (desktop or web)
- **Server**: Flask API server that interfaces with opea-docker services

All external service calls (LLM, TTS, ASR, image generation, database) are routed through the opea-docker API endpoints.

## Directory Structure

```
visual-novel/
├── renpy/                      # Ren'Py game files
│   ├── game/                   # Main game directory
│   │   ├── script.rpy          # Main script file
│   │   ├── characters.rpy      # Character definitions
│   │   ├── scenes/             # Scene scripts organized by lesson
│   │   ├── gui/                # GUI customization
│   │   ├── images/             # Static images
│   │   ├── audio/              # Audio files
│   │   └── python/             # Custom Python code
│   │       ├── api.py          # API communication
│   │       ├── jlpt.py         # JLPT N5 curriculum logic
│   │       └── progress.py     # Progress tracking
│   └── web/                    # Web export configuration
├── server/                     # Game server / API Gateway
│   ├── app.py                  # Main server application
│   ├── routes/                 # API routes
│   ├── models/                 # Data models
│   └── services/               # Service integrations
├── docker/                     # Docker configuration
├── curriculum/                 # JLPT N5 curriculum content
└── docs/                       # Documentation
```

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Ren'Py SDK 7.4.0+
- Docker and Docker Compose
- opea-docker running on your system

### Local Development

1. Set up a Python virtual environment for the server:

```bash
cd visual-novel/server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the server locally:

```bash
python app.py
```

3. Open the Ren'Py project in the Ren'Py SDK for client-side development.

## Adding New Content

### Adding a New Lesson

1. Create a new scene script in `renpy/game/scenes/`
2. Update the JLPT curriculum in `renpy/game/python/jlpt.py`
3. Add the lesson to the main menu in `script.rpy`

### Adding New Characters

1. Define the character in `characters.rpy`
2. Generate character images using the image generation API
3. Add character sprites to `renpy/game/images/characters/`

## API Integration

All external service calls are centralized through the `api.py` module, which communicates with the server's API endpoints. The server then routes these requests to the appropriate opea-docker services.

### API Service Module

The `APIService` class in `renpy/game/python/api.py` provides methods for:

- Text-to-speech generation
- Speech-to-text transcription
- Image generation
- LLM text generation
- Translation
- Database operations

### Adding a New API Service

To add a new API service:

1. Add the service endpoint to `api.py`
2. Create appropriate methods in the `APIService` class
3. Update the server's `app.py` to handle the new endpoints
4. Add any necessary service integration files in `server/services/`

## Working with opea-docker

The visual novel is designed to work with the opea-docker API for all external services. The integration is configured through environment variables in `docker-compose.yml`.

### opea-docker API Endpoints

The following opea-docker API endpoints are used:

- `/llm/text`: Text generation, translation, and conversation
- `/llm/vision`: Image understanding and description
- `/tts`: Text-to-speech conversion
- `/asr`: Speech-to-text transcription
- `/image/generate`: Image generation for backgrounds and characters
- `/embeddings`: Text embeddings for semantic search
- `/database`: Database operations (optional)

## Testing

### Server Testing

To run tests for the server:

```bash
cd visual-novel/server
python -m unittest discover tests
```

### Ren'Py Testing

Ren'Py provides a testing framework that can be used to test game functionality:

1. Create test scripts in `renpy/game/tests/`
2. Run tests using the Ren'Py SDK

## Building for Production

### Desktop Build

To build the desktop version:

1. Use the Ren'Py SDK to build for your target platforms (Windows, macOS, Linux)
2. Package the server as a separate application or use a hosted server

### Web Build

To build the web version:

1. Use the Ren'Py SDK to build the web version
2. Copy the web build to `renpy/web/`
3. Deploy using the Docker setup:

```bash
cd visual-novel/docker
docker-compose up -d
```

## Contribution Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

## Resources

- [Ren'Py Documentation](https://www.renpy.org/doc/html/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [opea-docker API Documentation](https://github.com/yourusername/opea-docker)
- [JLPT N5 Resources](https://jlptsensei.com/jlpt-n5-study-material/)