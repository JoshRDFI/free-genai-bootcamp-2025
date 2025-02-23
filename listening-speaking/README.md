## Tech Stack
The JLPT Listening Practice App is built using the following technologies:
1. **Python**: The primary programming language used for both the backend and frontend.
2. **Streamlit**: A Python-based framework for building interactive web applications, used for the frontend.
3. **FastAPI**: A modern, fast (high-performance) web framework for building APIs, used for the backend.
4. **SQLite**: A lightweight, file-based database used to store transcripts, questions, and other data.
5. **YouTube Transcript API**: A library used to extract transcripts from YouTube videos.
6. **Coqui TTS**: An open-source text-to-speech engine used to generate audio for questions.
7. **Docker**: Used to containerize the application for easier deployment and scalability.

## Features
1. **YouTube Video Processing**: Extract transcripts from YouTube videos and generate listening comprehension questions.
2. **Interactive Practice**: Practice listening comprehension with generated questions and audio.
3. **Audio Generation**: Generate audio for questions using Coqui TTS.
4. **Content Validation**: Ensure transcripts and questions meet quality and appropriateness standards.
5. **Saved Questions**: Access previously generated questions for continued practice.

## Directory Structure
The project is organized as follows:
listening-speaking/
├── backend/
│   ├── __init__.py
│   ├── app.py                # Main backend entrypoint.
|   ├── data/
|   │   ├── questions/          # Stores question text files 
|   │   ├── transcripts/        # Stores transcript text files
│   │   └── stored_questions.json  # JSON list of questions that is added to with each transcription
│   ├── youtube/
│   │   ├── __init__.py
│   │   └── get_transcript.py # Handles YouTube transcript extraction.
│   ├── asr/
│   │   ├── __init__.py
│   │   └── asr_engine.py     # OpenWhisper-based ASR implementation.
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── chat.py           # LLM chat interface (API at port 9000).
│   │   └── question_generator.py  # Generates listening comprehension questions.
│   ├── tts/
|   |   ├── coqui_models/ # Place downloaded Coqui TTS models here
│   │   │   ├── model.pth
│   │   │   ├── config.json
│   │   │   ├── speakers.pth (if multi-speaker)
│   │   │   └── vocoder.pth
│   │   ├── __init__.py
│   │   ├── audio_generator.py   # Generates audio using Piper TTS or Coqui TTS.
│   │   └── tts_engine.py        # Wrapper for TTS engines.
│   ├── database/
│   │   ├── __init__.py
│   │   └── knowledge_base.py    # SQLite3 integration for transcripts, questions, etc.
│   ├── agent/
│   │   ├── __init__.py
│   │   └── task_agent.py        # Coordinates ASR, transcript, LLM, and TTS tasks.
│   ├── guardrails/
│   │   ├── __init__.py
│   │   └── rules.py             # Guardrails for filtering inappropriate content.
│   └── utils/
│       ├── __init__.py
│       └── helper.py            # Common helper functions.
├── frontend/
│   └── streamlit_app.py         # Streamlit frontend (to be built later).
├── Dockerfile                   # Backend Dockerfile. -- unused ATM, for future integration
├── docker-compose.yml           # Coordinates LLM container and backend services. -- unused ATM, for future integration
├── requirements.txt             # Python dependencies.
└── README.md                    # Project overview and setup instructions.
