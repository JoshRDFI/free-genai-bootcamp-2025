# backend/tts/tts_engine.py

from typing import Optional, Dict, List
import os
import json
import numpy as np
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from backend.config import ServiceConfig
import logging
import base64

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        """Initialize TTS engine with retry configuration"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=ServiceConfig.RETRY_CONFIG["max_retries"],
            backoff_factor=ServiceConfig.RETRY_CONFIG["backoff_factor"],
            status_forcelist=ServiceConfig.RETRY_CONFIG["status_forcelist"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def synthesize_speech(self, text: str, voice_id: str = "default", language: str = "ja") -> Optional[bytes]:
        """
        Synthesize speech from text using TTS service.
        
        Args:
            text (str): Text to synthesize
            voice_id (str): Voice ID to use
            language (str): Language code (default: Japanese)
            
        Returns:
            Optional[bytes]: Audio data if successful, None otherwise
        """
        try:
            endpoint = ServiceConfig.get_endpoint("tts", "synthesize")
            if not endpoint:
                logger.error("TTS synthesize endpoint not configured")
                return None

            response = self.session.post(
                endpoint,
                json={
                    "text": text,
                    "voice_id": voice_id,
                    "language": language
                },
                timeout=ServiceConfig.get_timeout("tts")
            )
            response.raise_for_status()
            
            # Decode base64 audio data
            audio_data = base64.b64decode(response.json()["audio"])
            return audio_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return None

    def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices from TTS service.
        
        Returns:
            List[Dict]: List of available voices
        """
        try:
            endpoint = ServiceConfig.get_endpoint("tts", "voices")
            if not endpoint:
                logger.error("TTS voices endpoint not configured")
                return []

            response = self.session.get(
                endpoint,
                timeout=ServiceConfig.get_timeout("tts")
            )
            response.raise_for_status()
            return response.json().get("voices", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []

    def save_audio(self, audio_data: bytes, filepath: str) -> bool:
        """
        Save audio data to file.
        
        Args:
            audio_data (bytes): Audio data to save
            filepath (str): Path to save the audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            return False

    def generate_silence(self, duration_ms: int, output_path: str) -> bool:
        """
        Generate a silent audio segment.

        Args:
        duration_ms: Duration in milliseconds
        output_path: Path to save the audio file
        """
        try:
            sample_rate = 22050  # Standard sample rate
            num_samples = int((duration_ms / 1000) * sample_rate)
            silence = np.zeros(num_samples, dtype=np.float32)

            # Save as WAV file
            import soundfile as sf
            sf.write(output_path, silence, sample_rate)

            return True
        except Exception as e:
            logger.error(f"Error generating silence: {str(e)}")
            return False

    def combine_audio_files(self, audio_files: List[str], output_path: str) -> bool:
        """
        Combine multiple audio files into one.

        Args:
        audio_files: List of audio file paths
        output_path: Path to save the combined audio
        """
        try:
            import soundfile as sf

            # Read the first file to get sample rate
            data, sample_rate = sf.read(audio_files[0])
            combined = list(data)

            # Append remaining files
            for audio_file in audio_files[1:]:
                data, _ = sf.read(audio_file)
                combined.extend(data)

            # Save combined audio
            sf.write(output_path, np.array(combined), sample_rate)

            return True
        except Exception as e:
            logger.error(f"Error combining audio files: {str(e)}")
            return False

    def validate_text(self, text: str) -> bool:
        """
        Validate if the text is suitable for TTS.
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if text is valid, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
        return len(text.strip()) > 0