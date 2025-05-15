# backend/tts/audio_generator.py

import os
import subprocess
from typing import List, Optional
import tempfile
import re
from TTS.api import TTS  # For Coqui TTS

class AudioGenerator:
    def __init__(self, tts_engine: str = "coqui", language: str = "ja"):
        """
        Initialize the TTS engine.
        Args:
        tts_engine (str): The TTS engine to use ("coqui").
        language (str): Language code (e.g., "ja" for Japanese).
        """
        self.tts_engine = tts_engine
        self.language = language

        if tts_engine == "coqui":
            try:
                # Set the TTS model path to data/tts_data
                os.environ["COQUI_TTS_MODEL_PATH"] = os.path.abspath("data/tts_data")
                
                # Initialize Coqui TTS with XTTS-v2.0.3
                self.tts = TTS("tts_models/multilingual/xtts_v2",
                             progress_bar=True,  # Show progress bar during download
                             gpu=True)
            except Exception as e:
                print(f"Error initializing Coqui TTS: {str(e)}")
                print("Make sure you have installed TTS with: pip install TTS")
                raise
        else:
            raise ValueError("Unsupported TTS engine. Use 'coqui'.")
        
        # Define the base directory for TTS
        tts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tts")

        # Define paths to voice reference files
        self.male_voice_path = os.path.join(tts_dir, "voices", "male_voice.wav")
        self.female_voice_path = os.path.join(tts_dir, "voices", "female_voice.wav")

        # Create audio output directory with absolute path
        self.audio_dir = os.path.abspath(os.path.join(os.getcwd(), "audio_output"))
        os.makedirs(self.audio_dir, exist_ok=True)

    def generate_audio_with_male_voice(self, text: str, output_file: str) -> Optional[str]:
        """
        Generate audio using the male voice reference.

        Args:
            text (str): The text to convert to speech
            output_file (str): Path to save the generated audio

        Returns:
            Optional[str]: Path to the generated audio file, or None if failed
        """
        try:
            # Ensure the male voice reference file exists
            if not os.path.exists(self.male_voice_path):
                print(f"Male voice reference file not found: {self.male_voice_path}")
                return None

            return self.generate_audio(text, output_file, speaker_wav=self.male_voice_path)
        except Exception as e:
            print(f"Error generating audio with male voice: {str(e)}")
            return None

    def generate_audio_with_female_voice(self, text: str, output_file: str) -> Optional[str]:
        """
        Generate audio using the female voice reference.

        Args:
            text (str): The text to convert to speech
            output_file (str): Path to save the generated audio

        Returns:
            Optional[str]: Path to the generated audio file, or None if failed
        """
        try:
            # Ensure the female voice reference file exists
            if not os.path.exists(self.female_voice_path):
                print(f"Female voice reference file not found: {self.female_voice_path}")
                return None

            return self.generate_audio(text, output_file, speaker_wav=self.female_voice_path)
        except Exception as e:
            print(f"Error generating audio with female voice: {str(e)}")
            return None

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text to remove inappropriate content and normalize for TTS.
        Args:
        text (str): Input text.
        Returns:
        str: Sanitized text.
        """
        # Remove inappropriate content
        foul_language_pattern = r"\b(badword1|badword2|badword3)\b"
        text = re.sub(foul_language_pattern, "[REDACTED]", text, flags=re.IGNORECASE)

        # Normalize text for better TTS processing
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s。、？！」]', '', text)  # Keep only Japanese punctuation

        return text

    def generate_audio(self, text: str, output_file: str, speaker_wav: Optional[str] = None) -> Optional[str]:
        """
        Generate audio from text using the TTS engine.
        Args:
        text (str): Input text.
        output_file (str): Path to save the generated audio.
        speaker_wav (str): Path to the speaker reference audio file.
        Returns:
        Optional[str]: Path to the generated audio file, or None if failed.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            sanitized_text = self.sanitize_text(text)
            if not sanitized_text:
                raise ValueError("Empty text after sanitization")

            self.tts.tts_to_file(
                text=sanitized_text,
                file_path=output_file,
                speaker_wav=speaker_wav,
                language=self.language
            )

            # Verify the file was created
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Failed to create audio file: {output_file}")

            return output_file

        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            # Clean up partial file if it exists
            if os.path.exists(output_file):
                os.remove(output_file)
            return None

    def combine_audio_files(self, audio_files: List[str], output_file: str) -> bool:
        """
        Combine multiple audio files into a single file using ffmpeg.
        Args:
        audio_files (List[str]): List of audio file paths.
        output_file (str): Path to save the combined audio.
        Returns:
        bool: True if successful, False otherwise.
        """
        file_list = None
        try:
            # Verify all input files exist
            for audio_file in audio_files:
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile("w", delete=False, encoding='utf-8') as f:
                for audio_file in audio_files:
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")
                file_list = f.name

            # Combine audio files using ffmpeg
            subprocess.run(
                ["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list,
                 "-c", "copy", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        except Exception as e:
            print(f"Error combining audio files: {str(e)}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return False

        finally:
            # Clean up temporary file list
            if file_list and os.path.exists(file_list):
                os.remove(file_list)

    def generate_silence(self, duration_ms: int) -> str:
        """
        Generate a silent audio file of specified duration.
        Args:
        duration_ms (int): Duration of silence in milliseconds.
        Returns:
        str: Path to the generated silent audio file.
        """
        output_file = os.path.join(self.audio_dir, f"silence_{duration_ms}ms.mp3")
        try:
            if not os.path.exists(output_file):
                subprocess.run(
                    ["ffmpeg", "-f", "lavfi",
                     "-i", f"anullsrc=r=24000:cl=mono:d={duration_ms / 1000}",
                     "-c:a", "libmp3lame", "-b:a", "48k", output_file],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return output_file
        except Exception as e:
            print(f"Error generating silence: {str(e)}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None