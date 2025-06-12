# LLM text service integration

import requests
import json
import os
import httpx
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with the LLM Text service"""
    
    def __init__(self, base_url=None):
        self.ollama_url = base_url or os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        
    async def generate_text(self, prompt, max_tokens=1000):
        try:
            response = await httpx.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None

    async def explain_text(self, text):
        try:
            response = await httpx.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that explains Japanese text in simple terms."},
                        {"role": "user", "content": f"Please explain this Japanese text in simple terms: {text}"}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error explaining text: {e}")
            return None