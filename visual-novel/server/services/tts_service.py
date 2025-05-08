# TTS service integration

import requests
import json
import os

class TTSService:
    """Service for interacting with the TTS service"""
    
    def __init__(self, base_url=None):
        # Use the direct TTS service URL
        self.tts_url = base_url or os.environ.get('TTS_URL', 'http://localhost:9200')
        
    def generate_speech(self, text, voice="default", language="ja"):
        """Generate speech from text"""
        try:
            response = requests.post(
                f"{self.tts_url}/generate",
                json={
                    "text": text,
                    "voice": voice,
                    "language": language
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling TTS service: {e}")
            return {"error": str(e)}
    
    def get_available_voices(self):
        """Get list of available voices"""
        try:
            response = requests.get(
                f"{self.tts_url}/voices",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling TTS service: {e}")
            return {"error": str(e)}