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
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", None)
                
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return None

# Create singleton instance
_translator = None

def get_translator() -> Translator:
    """Get the singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator 