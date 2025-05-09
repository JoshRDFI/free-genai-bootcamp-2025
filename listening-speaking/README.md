# JLPT Listening Practice

A comprehensive application for practicing Japanese listening comprehension using YouTube videos and AI-generated content.

## Features

1. **YouTube Video Processing**
   - Extract transcripts from YouTube videos
   - Generate listening comprehension questions
   - Content validation for appropriateness

2. **Interactive Practice**
   - Practice with generated questions
   - Audio playback for questions
   - Multiple choice answers
   - Immediate feedback

3. **AI-Powered Features**
   - Text-to-speech for questions using Coqui TTS
   - Image generation for visual context
   - LLM-powered question generation
   - ASR for speech recognition

4. **Progress Tracking**
   - Save and access previous questions
   - Track learning progress
   - Review past practice sessions

## Tech Stack

- **Python**: Primary programming language
- **Streamlit**: Frontend framework
- **FastAPI**: Backend API framework
- **SQLite**: Database for storing data
- **Docker**: Containerization
- **Coqui TTS**: Text-to-speech engine
- **OpenWhisper**: Speech recognition
- **YouTube Transcript API**: Video transcript extraction

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- FFmpeg (for audio processing)

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure your environment variables in `.env`:
   - `BACKEND_PORT`: Port for the FastAPI backend (default: 8180)
   - `BASE_URL`: Base URL for the application (default: http://localhost)
   - `DATA_DIR`: Directory for storing application data (default: ./data)
   - `LOGS_DIR`: Directory for log files (default: ./backend/logs)
   - `AUDIO_DIR`: Directory for audio files (default: ./data/audio)
   - `IMAGES_DIR`: Directory for generated images (default: ./data/images)
   - `TRANSCRIPTS_DIR`: Directory for video transcripts (default: ./data/transcripts)
   - `QUESTIONS_DIR`: Directory for generated questions (default: ./data/questions)
   - Service ports and URLs for:
     - LLM Text Service (default: 9000)
     - TTS Service (default: 9200)
     - ASR Service (default: 9300)
     - Vision Service (default: 9100)
     - Embedding Service (default: 6000)
   - `LOG_LEVEL`: Logging level (default: INFO)

3. Run the environment setup script:
   ```bash
   python setup_env.py
   ```
   This will:
   - Create necessary directories
   - Validate your .env file
   - Set up the basic environment structure

Note: The `.env` file is ignored by git for security. Each developer should create their own `.env` file based on `.env.example`. The setup script will validate that all required variables are present in your `.env` file.

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

The application can be started using the main launcher:
```bash
python3 run.py
```

Or you can run components individually:
```bash
# Setup database
python3 run.py --setup

# Start backend server
python3 run.py --backend

# Start frontend
python3 run.py --frontend
```

### Docker Services

The application requires several Docker services to be running:
- LLM Service (port 9000)
- TTS Service (port 9200)
- ASR Service (port 9300)
- Vision Service (port 9100)

These services are managed by the main launcher and should start automatically.

## Project Structure

For detailed information about the project structure and file organization, please refer to `project-layout.txt`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
