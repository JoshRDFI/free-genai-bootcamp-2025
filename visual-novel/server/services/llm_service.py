# LLM text service integration

import requests
import json
import os

class LLMService:
    """Service for interacting with the LLM Text service"""
    
    def __init__(self, base_url=None):
        # Use the opea-docker API endpoint
        self.base_url = base_url or os.environ.get('OPEA_API_BASE_URL', 'http://opea-api-gateway:8000')
        self.llm_text_url = f"{self.base_url}/llm/text"
        
    def generate_dialogue(self, context, characters, length=200):
        """Generate dialogue based on context and characters"""
        try:
            response = requests.post(
                f"{self.llm_text_url}/generate",
                json={
                    "context": context,
                    "characters": characters,
                    "max_length": length
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling LLM service: {e}")
            return {"error": str(e)}
    
    def explain_grammar(self, grammar_point, language="en"):
        """Get explanation for a grammar point"""
        try:
            response = requests.post(
                f"{self.llm_text_url}/explain",
                json={
                    "grammar_point": grammar_point,
                    "language": language
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling LLM service: {e}")
            return {"error": str(e)}