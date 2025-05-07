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