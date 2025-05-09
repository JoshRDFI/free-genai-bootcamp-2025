import os
from typing import Dict, Any

class ServiceConfig:
    """Central configuration for all services"""
    
    # Backend port
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8180"))
    
    # Service ports from docker-compose
    LLM_TEXT_PORT = int(os.getenv("LLM_TEXT_PORT", "9000"))
    TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", "9200"))
    ASR_SERVICE_PORT = int(os.getenv("ASR_SERVICE_PORT", "9300"))
    LLM_VISION_PORT = int(os.getenv("LLM_VISION_PORT", "9100"))
    EMBEDDING_SERVICE_PORT = int(os.getenv("EMBEDDING_SERVICE_PORT", "6000"))
    
    # Service base URLs
    BASE_URL = "http://localhost"
    BACKEND_URL = f"{BASE_URL}:{BACKEND_PORT}"
    LLM_TEXT_URL = f"{BASE_URL}:{LLM_TEXT_PORT}"
    TTS_URL = f"{BASE_URL}:{TTS_SERVICE_PORT}"
    ASR_URL = f"{BASE_URL}:{ASR_SERVICE_PORT}"
    VISION_URL = f"{BASE_URL}:{LLM_VISION_PORT}"
    EMBEDDING_URL = f"{BASE_URL}:{EMBEDDING_SERVICE_PORT}"
    
    # API endpoints
    ENDPOINTS = {
        "llm": {
            "generate": f"{LLM_TEXT_URL}/generate",
            "validate": f"{LLM_TEXT_URL}/validate",
            "analyze": f"{LLM_TEXT_URL}/analyze",
            "embed": f"{LLM_TEXT_URL}/embed"
        },
        "tts": {
            "synthesize": f"{TTS_URL}/synthesize",
            "voices": f"{TTS_URL}/voices"
        },
        "asr": {
            "transcribe": f"{ASR_URL}/transcribe",
            "languages": f"{ASR_URL}/languages"
        },
        "vision": {
            "analyze": f"{VISION_URL}/analyze",
            "generate": f"{VISION_URL}/generate"
        },
        "embedding": {
            "embed": f"{EMBEDDING_URL}/embed"
        }
    }
    
    # Request timeouts (in seconds)
    TIMEOUTS = {
        "default": 30,
        "llm": 60,
        "tts": 120,
        "asr": 60,
        "vision": 60,
        "embedding": 30
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