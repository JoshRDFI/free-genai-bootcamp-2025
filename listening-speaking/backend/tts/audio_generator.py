import os
import subprocess
from typing import List, Optional
import tempfile
import re
from TTS.api import TTS  # For Coqui TTS
# Uncomment below if using Piper TTS
# from tts import TTS as PiperTTS

class AudioGenerator:
    def __init__(self, tts_engine: str = "coqui", language: str = "ja"):
        """
        Initialize the TTS engine.
        Args:
            tts_engine (str): The TTS engine to use ("coqui" or "piper").
            language (str): Language code (e.g., "ja" for Japanese).
        """
        self.tts_engine = tts_engine
        self.language = language

        if tts_engine == "coqui":
            # Initialize Coqui TTS
            self.tts = TTS(model_name="tts_models/ja/kokoro/tacotron2-DDC", gpu=False)
        elif tts_engine == "piper":
            # Initialize Piper TTS (uncomment if using Piper)
            # self.tts = PiperTTS(model_path="path_to_piper_model")
            raise NotImplementedError("Piper TTS is not yet implemented in this example.")
        else:
            raise ValueError("Unsupported TTS engine. Use 'coqui' or 'piper'.")

        # Create audio output directory
        self.audio_dir = os.path.join(os.getcwd(), "audio_output")
        os.makedirs(self.audio_dir, exist_ok=True)

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text to remove inappropriate content.
        Args:
            text (str): Input text.
        Returns:
            str: Sanitized text.
        """
        # Example regex to remove foul language
        foul_language_pattern = r"\b(badword1|badword2|badword3)\b"  # Replace with actual words
        sanitized_text = re.sub(foul_language_pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        return sanitized_text

    def generate_audio(self, text: str, output_file: str) -> Optional[str]:
        """
        Generate audio from text using the TTS engine.
        Args:
            text (str): Input text.
            output_file (str): Path to save the generated audio.
        Returns:
            Optional[str]: Path to the generated audio file, or None if failed.
        """
        try:
            sanitized_text = self.sanitize_text(text)

            if self.tts_engine == "coqui":
                # Generate audio using Coqui TTS
                self.tts.tts_to_file(text=sanitized_text, file_path=output_file)
            elif self.tts_engine == "piper":
                # Generate audio using Piper TTS (uncomment if using Piper)
                # self.tts.synthesize(sanitized_text, output_file)
                pass

            return output_file
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
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
        try:
            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile("w", delete=False) as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
                file_list = f.name

            # Combine audio files using ffmpeg
            subprocess.run(
                ["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list, "-c", "copy", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            print(f"Error combining audio files: {str(e)}")
            return False
        finally:
            # Clean up temporary file list
            if os.path.exists(file_list):
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
        if not os.path.exists(output_file):
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "lavfi",
                    "-i",
                    f"anullsrc=r=24000:cl=mono:d={duration_ms / 1000}",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "48k",
                    output_file,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return output_file