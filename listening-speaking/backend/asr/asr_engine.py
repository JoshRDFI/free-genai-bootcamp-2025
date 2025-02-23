import whisper
import os
import subprocess
from typing import Optional
import re

class ASREngine:
    def __init__(self, model_name: str = "base"):
        """
        Initialize the ASR engine with OpenWhisper.
        Args:
            model_name (str): Whisper model to use (e.g., "base", "small", "medium", "large").
        """
        self.model = whisper.load_model(model_name)

    def convert_to_wav(self, input_file: str, output_file: str) -> bool:
        """
        Convert audio to WAV format using ffmpeg.
        Args:
            input_file (str): Path to the input audio file.
            output_file (str): Path to the output WAV file.
        Returns:
            bool: True if conversion is successful, False otherwise.
        """
        try:
            subprocess.run(
                ["ffmpeg", "-i", input_file, "-ar", "16000", "-ac", "1", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            print(f"Error converting audio to WAV: {str(e)}")
            return False

    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio using OpenWhisper.
        Args:
            audio_file (str): Path to the audio file.
        Returns:
            Optional[str]: Transcribed text if successful, None otherwise.
        """
        try:
            # Transcribe audio
            result = self.model.transcribe(audio_file)
            transcript = result.get("text", "").strip()
            return transcript
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            return None

    def sanitize_transcription(self, text: str) -> str:
        """
        Sanitize transcription output using regex guardrails.
        Args:
            text (str): Transcribed text.
        Returns:
            str: Sanitized text.
        """
        # Example regex rules to remove foul language or inappropriate content
        foul_language_pattern = r"\b(badword1|badword2|badword3)\b"  # Replace with actual words
        sanitized_text = re.sub(foul_language_pattern, "[REDACTED]", text, flags=re.IGNORECASE)

        # Additional sanitization rules can be added here
        return sanitized_text

    def process_audio(self, input_file: str) -> Optional[str]:
        """
        Process an audio file: convert to WAV, transcribe, and sanitize.
        Args:
            input_file (str): Path to the input audio file.
        Returns:
            Optional[str]: Sanitized transcription if successful, None otherwise.
        """
        # Temporary WAV file
        temp_wav = "temp_audio.wav"

        try:
            # Convert to WAV
            if not self.convert_to_wav(input_file, temp_wav):
                print("Failed to convert audio to WAV format.")
                return None

            # Transcribe audio
            transcript = self.transcribe_audio(temp_wav)
            if not transcript:
                print("Failed to transcribe audio.")
                return None

            # Sanitize transcription
            sanitized_transcript = self.sanitize_transcription(transcript)
            return sanitized_transcript
        finally:
            # Clean up temporary WAV file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)