# backend/tts/tts_engine.py

from typing import Optional, Dict, List
import os
import json
from TTS.api import TTS
import torch
import numpy as np
from datetime import datetime

class TTSEngine:
    def __init__(self, model_path: str = "backend/tts/coqui_models"):
        """Initialize TTS engine with Coqui TTS"""
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize TTS
        try:
            self.tts = TTS(model_path=os.path.join(model_path, "model.pth"),
                          config_path=os.path.join(model_path, "config.json"),
                          progress_bar=False,
                          gpu=torch.cuda.is_available())
        except Exception as e:
            print(f"Error initializing TTS: {str(e)}")
            self.tts = None

    def load_speaker_config(self) -> Dict:
        """Load speaker configuration if available"""
        config_path = os.path.join(self.model_path, "speaker_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def generate_audio(self, text: str, output_path: str,
                      speaker_id: Optional[int] = None,
                      speed: float = 1.0) -> bool:
        """
        Generate audio from text using Coqui TTS.

        Args:
            text: Japanese text to convert to speech
            output_path: Path to save the audio file
            speaker_id: Speaker ID for multi-speaker models
            speed: Speech rate multiplier
        """
        if not self.tts:
            print("TTS engine not initialized")
            return False

        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Generate audio
            self.tts.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_id=speaker_id,
                speed=speed
            )

            return os.path.exists(output_path)
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return False

    def generate_silence(self, duration_ms: int, output_path: str) -> bool:
        """
        Generate a silent audio segment.

        Args:
            duration_ms: Duration in milliseconds
            output_path: Path to save the audio file
        """
        try:
            sample_rate = 22050  # Standard sample rate for Coqui TTS
            num_samples = int((duration_ms / 1000) * sample_rate)
            silence = np.zeros(num_samples, dtype=np.float32)

            # Save as WAV file
            import soundfile as sf
            sf.write(output_path, silence, sample_rate)

            return True
        except Exception as e:
            print(f"Error generating silence: {str(e)}")
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
            print(f"Error combining audio files: {str(e)}")
            return False

    def get_available_speakers(self) -> List[str]:
        """Get list of available speakers for multi-speaker models"""
        if not self.tts:
            return []

        try:
            return self.tts.speakers
        except:
            return []

    def validate_text(self, text: str) -> bool:
        """
        Validate text before TTS processing.

        Args:
            text: Text to validate
        """
        if not text:
            return False

        # Check for Japanese characters
        if not any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
            return False

        return True