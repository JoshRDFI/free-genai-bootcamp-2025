# Language Learning Portal

A web-based portal for managing your Japanese language learning journey. This application provides a central interface to track your progress, manage vocabulary, and integrate with other learning tools.

## Components

- **Frontend**: React-based web interface
- **Backend**: FastAPI-based REST API
- **Database**: SQLite database for user data and progress tracking

## Requirements

- Python 3.10 or higher
- Node.js and npm
- WSL2 (if running on Windows)

## Setup

The setup process is automated through the main project's setup script. It will:

1. Create a Python virtual environment
2. Install Python dependencies
3. Install Node.js dependencies
4. Set up the database
5. Configure the development environment

## Development

To start the development server:

```bash
./start_portal.py
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Architecture

- Frontend: React + TypeScript
- Backend: FastAPI + SQLAlchemy
- Authentication: JWT-based
- Database: SQLite with async support

## Audio Generation and Lesson Creation

The portal includes tools for generating Japanese audio lessons using Text-to-Speech (TTS) technology.

### Prerequisites

- TTS Docker container running on port 9200
- ffmpeg (optional, for MP3 conversion)

### Available Scripts

#### 1. Direct TTS Generation

Use `generate_japanese_tts.py` to generate individual audio files:

```bash
python generate_japanese_tts.py --text "こんにちは" --filename "greeting" --voice female
```

Parameters:
- `--text`: Japanese text to convert to speech
- `--filename`: Output filename (without extension)
- `--voice`: Voice selection (male/female)

#### 2. Interactive Lesson Creation

Use `create_lesson.py` for an interactive lesson creation process:

```bash
python create_lesson.py
```

This script will:
- Prompt for lesson title and description
- Allow multi-line Japanese text input
- Let you choose the voice (male/female)
- Generate audio files
- Store lesson metadata

### File Structure

Generated files are stored in:
- Audio files: `frontend/public/audio/`
- Lesson metadata: `frontend/public/lessons/metadata.json`

### Usage Notes

- Audio files are generated in MP3 format (or WAV if ffmpeg is not available)
- Lesson metadata includes title, description, text content, and voice selection
- All generated content is immediately available to the frontend application
