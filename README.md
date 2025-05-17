# Free GenAI Bootcamp 2025 - JLPT Language Tutor Project

This repository contains a comprehensive system for learning Japanese, focusing on JLPT N5-level content. It integrates various AI-powered services, including LLMs, TTS, ASR, and image generation, to provide an interactive and engaging learning experience.

---

## **Tech Stack**
- **Python**: Primary programming language for backend and frontend services.
- **Streamlit**: Framework for building interactive web applications.
- **FastAPI**: High-performance web framework for backend APIs.
- **SQLite**: Lightweight database for storing application data.
- **Docker**: Containerization for services and deployment.
- **Ren'Py**: Visual novel engine for the frontend.
- **Coqui TTS**: Open-source text-to-speech engine.
- **Hugging Face Transformers**: For LLM-based content generation.
- **MangaOCR**: OCR for Japanese text recognition.

---

## **Features**
1. **Interactive Learning**: 
   - Vocabulary practice, sentence generation, and listening comprehension.
   - Visual novel-style gameplay for immersive learning.
2. **AI-Powered Services**:
   - LLM for sentence generation and translations.
   - TTS for audio generation.
   - ASR for speech recognition.
   - Image generation for visual aids.
3. **Curriculum Integration**:
   - Covers JLPT N5 grammar, vocabulary, and cultural elements.
   - Tracks progress and provides assessments.
4. **Extensibility**:
   - Modular architecture for adding new features and services.
   - Dockerized services for easy deployment.

---

## **Services**
### **Language Portal** (Standalone)
- Original vocabulary management and study portal (superseded by Vocabulary Generator)
- Available at http://localhost:5173
- **Note**: This is a standalone program that requires its own setup and runs independently of the main application
- Setup:
  ```bash
  cd lang-portal
  chmod +x setup.sh
  ./setup.sh
  ```
- Run:
  ```bash
  ./start_portal.py
  ```

### **opea-docker Microservices**
- **LLM Text Service**: http://localhost:9000/v1/chat/completions
- **TTS Service**: http://localhost:9200/tts
- **ASR Service**: http://localhost:9300/asr
- **Vision Service**: http://localhost:9100/v1/vision
- **Embeddings Service**: http://localhost:6000/embed
- **Guardrails Service**: http://localhost:9400/v1/guardrails
- **ChromaDB**: http://localhost:8050

### **Visual Novel**
- Interactive gameplay powered by Ren'Py.
- API integration with opea-docker services for dynamic, AI generated content.

### **Listening and Speaking Practice**
- Extracts transcripts from YouTube videos.
- Generates listening comprehension questions and audio.

### **Vocabulary Generator**
- AI-assisted vocabulary generation and validation.
- Tracks progress through JLPT levels.

### **Writing Practice**
- Sentence generation and grading using LLMs.
- OCR for handwritten Japanese text.

## **Quick Start**

For first-time setup, run:

```bash
python3 first_start.py
```

This script will:
1. Create all necessary data directories
2. Download required models:
   - TTS (XTTS v2)
   - MangaOCR
   - Ollama (llama3.2)
   - ASR (Whisper)
3. Build all Docker images
4. Start all required services
5. Launch the main application

## **Manual Setup**

If you prefer to set up components manually, follow these steps:

1. Create data directories:
```bash
mkdir -p data/{tts_data,mangaocr_models,asr_data,waifu,embeddings,chroma_data,ollama_data,shared_db}
```

2. Download models:
```bash
# Download TTS and MangaOCR models
python3 opea-docker/setup_tts.py
python3 opea-docker/setup_mangaocr.py

# Pull Ollama model
docker exec ollama-server ollama pull llama3.2

# Download ASR model
docker exec asr python3 -c 'from transformers import WhisperForConditionalGeneration; WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")'
```

3. Build Docker images:
```bash
cd opea-docker
chmod +x build-images.sh
./build-images.sh
```

4. Start services:
```bash
docker compose up -d
```

5. Start the application:
```bash
streamlit run project_start.py
```

## **Requirements**

- Python 3.10+
- Docker
- NVIDIA GPU with CUDA support
- WSL2 (for Windows users)

## **Troubleshooting**

If you encounter any issues:

1. Check if all Docker services are running:
```bash
docker compose ps
```

2. Verify model files are present:
```bash
ls data/tts_data
ls data/mangaocr_models
```

3. Check service logs:
```bash
docker compose logs
```

## **License**

MIT License