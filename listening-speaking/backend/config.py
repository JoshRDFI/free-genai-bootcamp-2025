import os
from typing import Dict, Any

class ServiceConfig:
    """Central configuration for all services"""
    
    # Backend port
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8180"))
    
    # Service ports from docker-compose
    LLM_TEXT_PORT = int(os.getenv("LLM_TEXT_PORT", "11434"))
    EMBEDDING_SERVICE_PORT = int(os.getenv("EMBEDDING_SERVICE_PORT", "6000"))
    TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", "9200"))
    ASR_SERVICE_PORT = int(os.getenv("ASR_SERVICE_PORT", "9300"))
    MANGAOCR_PORT = int(os.getenv("MANGAOCR_PORT", "9100"))
    LLM_VISION_PORT = int(os.getenv("LLM_VISION_PORT", "9101"))
    WAIFU_DIFFUSION_PORT = int(os.getenv("WAIFU_DIFFUSION_PORT", "9500"))
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
    
    # Service base URLs
    BASE_URL = os.getenv("BASE_URL", "http://localhost")
    BACKEND_URL = f"{BASE_URL}:{BACKEND_PORT}"
    EMBEDDING_URL = f"{BASE_URL}:{EMBEDDING_SERVICE_PORT}"
    LLM_TEXT_URL = f"{BASE_URL}:{LLM_TEXT_PORT}/api/chat"
    TTS_URL = f"{BASE_URL}:{TTS_SERVICE_PORT}"
    ASR_URL = f"{BASE_URL}:{ASR_SERVICE_PORT}"
    MANGAOCR_URL = f"{BASE_URL}:{MANGAOCR_PORT}"
    VISION_URL = f"{BASE_URL}:{LLM_VISION_PORT}"
    EMBEDDING_URL = f"{BASE_URL}:{EMBEDDING_SERVICE_PORT}"
    WAIFU_DIFFUSION_URL = f"{BASE_URL}:{WAIFU_DIFFUSION_PORT}"
    CHROMADB_URL = f"{BASE_URL}:{CHROMADB_PORT}"
    
    # API endpoints
    ENDPOINTS = {
        "llm": {
            "generate": LLM_TEXT_URL,
            "validate": f"{BASE_URL}:{LLM_TEXT_PORT}/validate",
            "analyze": f"{BASE_URL}:{LLM_TEXT_PORT}/analyze",
            "embed": f"{BASE_URL}:{EMBEDDING_SERVICE_PORT}/embed"
        },
        "tts": {
            "synthesize": f"{TTS_URL}/synthesize",
            "voices": f"{TTS_URL}/voices"
        },
        "asr": {
            "transcribe": f"{ASR_URL}/asr",
            "languages": f"{ASR_URL}/languages"
        },
        "vision": {
            "analyze_manga": f"{MANGAOCR_URL}/analyze",  # MangaOCR for Japanese text recognition
            "analyze_image": f"{VISION_URL}/analyze",  # LLaVA for general image analysis
            "generate": f"{WAIFU_DIFFUSION_URL}/generate"  # Waifu-diffusion for image generation
        },
        "embedding": {
            "embed": f"{EMBEDDING_URL}/embed"
        },
        "chromadb": {
            "base": CHROMADB_URL
        }
    }
    
    # Request timeouts (in seconds)
    TIMEOUTS = {
        "default": 30,
        "llm": 60,
        "tts": 120,
        "asr": 60,
        "vision": 60,
        "embedding": 30,
        "waifu-diffusion": 120,  # Longer timeout for image generation
        "chromadb": 30  # Timeout for ChromaDB operations
    }
    
    # Retry configuration
    RETRY_CONFIG = {
        "max_retries": 3,
        "backoff_factor": 0.5,
        "status_forcelist": [500, 502, 503, 504]
    }
    
    @classmethod
    def get_endpoint(cls, service: str, action: str) -> str:
        """Get the full endpoint URL for a service action"""
        return cls.ENDPOINTS.get(service, {}).get(action)
    
    @classmethod
    def get_timeout(cls, service: str) -> int:
        """Get the timeout for a service"""
        return cls.TIMEOUTS.get(service, cls.TIMEOUTS["default"])

    TTS_DATA_PATH = os.getenv("TTS_DATA_PATH", "data/tts_data")

    # LLM Configuration
    OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Service Endpoints
    SERVICE_ENDPOINTS = {
        "generate": OLLAMA_URL,
        "validate": OLLAMA_URL,
        "analyze": OLLAMA_URL,
        "translate": OLLAMA_URL,
        "tts": f"{BASE_URL}:{TTS_SERVICE_PORT}/tts",
        "asr": f"{BASE_URL}:{ASR_SERVICE_PORT}/asr",
        "image_gen": f"{BASE_URL}:{WAIFU_DIFFUSION_PORT}/generate",
    }

    # Service Timeouts (in seconds)
    SERVICE_TIMEOUTS = {
        "ollama": 30,
        "tts": 60,
        "asr": 30,
        "image_gen": 120,
    } 