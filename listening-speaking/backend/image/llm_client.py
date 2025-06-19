import requests
import logging
from backend.config import ServiceConfig

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """Initialize LLM client for translations"""
        self.session = requests.Session()

    def generate_response(self, prompt: str) -> str:
        """Generate response from LLM for translations"""
        try:
            response = self.session.post(
                f"{ServiceConfig.OLLAMA_URL}/api/chat",
                json={
                    "model": ServiceConfig.OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional Japanese to English translator. Translate the given Japanese text to English, maintaining the original meaning and context. Do not add any explanations, notes, or alternative translations. Only provide the direct translation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False
                },
                timeout=ServiceConfig.get_timeout("ollama")
            )
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return "" 