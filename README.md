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

## **Project Components**

### **1. Listening and Speaking Practice** (Port 8502)
- Extracts transcripts from YouTube videos
- Generates listening comprehension questions and audio
- Uses LLM, TTS, and ASR services

### **2. Vocabulary Generator** (Port 8503)
- AI-assisted vocabulary generation and validation
- Tracks progress through JLPT levels
- Uses LLM and embeddings services

### **3. Writing Practice** (Port 8504)
- Sentence generation and grading using LLMs
- OCR for handwritten Japanese text
- Uses LLM and vision services

### **4. Visual Novel**
- Interactive gameplay powered by Ren'Py
- AI-generated content using multiple services
- Uses all available AI services

### **5. Language Portal** (Port 5173, Standalone)
- Original vocabulary management portal
- Requires separate setup (see below)
- Uses npm/Node.js for frontend

### **Docker Services**
All components share these microservices:
- LLM Text Service (9000)
- TTS Service (9200)
- ASR Service (9300)
- Vision Service (9100)
- Embeddings Service (6000)
- Guardrails Service (9400)
- ChromaDB (8050)

---

## **Installation**

### **Prerequisites**
- Python 3.10+
- Docker with NVIDIA GPU support
- NVIDIA GPU with CUDA support
- WSL2 (for Windows users)

### **Quick Start**

1. **Initial Setup**:
```bash
python3 first_start.py
```
This will:
- Create all necessary data directories
- Set up virtual environments for each component
- Download required AI models
- Initialize databases
- Build and start Docker services

2. **Launch the Application**:
```bash
python3 project_start.py
```
This launches the main interface where you can start any component.

### **Language Portal Setup** (Optional)
The Language Portal is a standalone application:
```bash
cd lang-portal
chmod +x setup.sh
./setup.sh
python3 start_portal.py
```

---

## **Project Structure**

Each component has its own virtual environment:
- `.venv-main`: Main launcher environment
- `.venv-ls`: Listening-Speaking practice
- `.venv-vocab`: Vocabulary Generator
- `.venv-wp`: Writing Practice
- `.venv-vn`: Visual Novel
- `.venv-portal`: Language Portal backend

Docker services remain independent of these environments.

---

## **Troubleshooting**

1. **Virtual Environment Issues**:
   - If you encounter dependency conflicts, try removing the virtual environments and running `first_start.py` again
   - Each component's environment is isolated, so issues in one won't affect others

2. **Docker Services**:
```bash
# Check service status
docker compose ps

# View service logs
docker compose logs

# Restart services
docker compose down
docker compose up -d
```

3. **Model Files**:
```bash
# Verify model files
ls data/tts_data
ls data/mangaocr_models
ls data/asr_data
```

4. **Port Conflicts**:
   - Each component uses a specific port
   - Check if ports are already in use: `netstat -tulpn | grep <port>`
   - Kill process using a port: `fuser -k <port>/tcp`

5. **WSL2 Access**:
   - Access services using `localhost` from Windows browser
   - Ensure ports are not blocked by firewall
   - Don't use WSL IP address directly

---

## **License**

MIT License