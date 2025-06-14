"""
Translation module for Japanese text.
"""
import requests
from typing import Optional
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)

class Translator:
    """Handles translation of Japanese text."""
    
    def __init__(self):
        """Initialize the translator."""
        self.config = get_config()
        self.endpoint = self.config.get('ollama_endpoint', 'http://localhost:11434/api/generate')
        self.model = self.config.get('ollama_model', 'llama3.2')
    
    def translate(self, text: str) -> Optional[str]:
        """
        Translate Japanese text to English.
        
        Args:
            text: Japanese text to translate
            
        Returns:
            English translation or None if translation fails
        """
        try:
            prompts = self.config.get('prompts', {})
            system_prompt = prompts.get('translation', {}).get('system', '')
            user_prompt = prompts.get('translation', {}).get('user', '').format(text=text)
            
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=30  # Increased timeout for LLM response
            )
            
            if response.status_code == 200:
                result = response.json()
                translation = result.get("response", None)
                if translation:
                    return translation.strip()
                else:
                    logger.warning("LLM response did not contain translation")
                    return None
            else:
                logger.error(f"LLM API error: {response.status_code} {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        try:
            response = requests.get(
                self.endpoint.rsplit('/api/', 1)[0] + '/api/version',
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

# Create singleton instance
_translator = None

def get_translator() -> Translator:
    """Get the singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator 