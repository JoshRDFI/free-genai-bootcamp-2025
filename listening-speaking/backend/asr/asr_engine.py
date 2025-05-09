import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional, Dict, List
import os
from backend.config import ServiceConfig

logger = logging.getLogger(__name__)

class ASREngine:
    def __init__(self):
        """Initialize ASR engine with retry configuration"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=ServiceConfig.RETRY_CONFIG["max_retries"],
            backoff_factor=ServiceConfig.RETRY_CONFIG["backoff_factor"],
            status_forcelist=ServiceConfig.RETRY_CONFIG["status_forcelist"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def transcribe_audio(self, audio_data: bytes, language: str = "ja") -> Optional[Dict]:
        """
        Transcribe audio data using ASR service.
        
        Args:
            audio_data (bytes): Audio data to transcribe
            language (str): Language code (default: Japanese)
            
        Returns:
            Optional[Dict]: Transcription result if successful, None otherwise
        """
        try:
            endpoint = ServiceConfig.get_endpoint("asr", "transcribe")
            if not endpoint:
                logger.error("ASR transcribe endpoint not configured")
                return None

            files = {
                'audio': ('audio.wav', audio_data, 'audio/wav')
            }
            data = {
                'language': language
            }

            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=ServiceConfig.get_timeout("asr")
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages from ASR service.
        
        Returns:
            List[str]: List of supported language codes
        """
        try:
            endpoint = ServiceConfig.get_endpoint("asr", "languages")
            if not endpoint:
                logger.error("ASR languages endpoint not configured")
                return []

            response = self.session.get(
                endpoint,
                timeout=ServiceConfig.get_timeout("asr")
            )
            response.raise_for_status()
            return response.json().get("languages", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting supported languages: {str(e)}")
            return []

    def transcribe_file(self, filepath: str, language: str = "ja") -> Optional[Dict]:
        """
        Transcribe audio from file using ASR service.
        
        Args:
            filepath (str): Path to audio file
            language (str): Language code (default: Japanese)
            
        Returns:
            Optional[Dict]: Transcription result if successful, None otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                audio_data = f.read()
            return self.transcribe_audio(audio_data, language)
        except Exception as e:
            logger.error(f"Error reading audio file: {str(e)}")
            return None