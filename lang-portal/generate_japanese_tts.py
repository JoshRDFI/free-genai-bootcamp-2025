#!/usr/bin/env python3
"""
Script to generate Japanese TTS audio files using the TTS Docker container.
This script can be used to generate audio files for language lessons.
"""

import requests
import base64
import json
import time
import os
import argparse
from typing import Optional

# Configuration
TTS_CONTAINER_URL = "http://localhost:9200"  # Adjust if your container runs on different host/port
OUTPUT_DIR = "frontend/public/audio"  # Updated to point to frontend public audio directory

def create_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def generate_tts_audio(text: str, filename: str, voice_id: Optional[str] = None, language: str = "ja") -> bool:
    """
    Generate TTS audio using the container API

    Args:
        text: Text to convert to speech
        filename: Output filename (without extension)
        voice_id: Voice to use ('male', 'female', or None for default)
        language: Language code (default: 'ja' for Japanese)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare the request payload
        payload = {
            "text": text,
            "language": language,
            "speed": 1.0
        }

        if voice_id:
            payload["voice_id"] = voice_id

        print(f"Generating audio for: {filename}")
        print(f"Text: {text[:50]}{'...' if len(text) > 50 else ''}")

        # Make the API request
        response = requests.post(f"{TTS_CONTAINER_URL}/tts", json=payload, timeout=60)

        if response.status_code == 200:
            # Decode the base64 audio data
            audio_data = base64.b64decode(response.json()["audio"])

            # Save as WAV first (since the API returns WAV)
            wav_path = os.path.join(OUTPUT_DIR, f"{filename}.wav")
            with open(wav_path, "wb") as f:
                f.write(audio_data)

            print(f"✓ Successfully generated: {wav_path}")

            # Convert to MP3 if ffmpeg is available (optional)
            try:
                import subprocess
                mp3_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")
                subprocess.run([
                    "ffmpeg", "-i", wav_path, "-codec:a", "libmp3lame", 
                    "-b:a", "128k", mp3_path, "-y"
                ], check=True, capture_output=True)
                print(f"✓ Converted to MP3: {mp3_path}")
                # Remove WAV file after successful conversion
                os.remove(wav_path)
            except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
                print(f"⚠ MP3 conversion failed or ffmpeg not available. Keeping WAV file: {wav_path}")

            return True
        else:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def check_tts_service():
    """Check if the TTS service is running"""
    try:
        response = requests.get(f"{TTS_CONTAINER_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ TTS service is running")
            return True
        else:
            print(f"✗ TTS service returned HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to TTS service: {e}")
        print(f"Make sure your TTS container is running on {TTS_CONTAINER_URL}")
        return False

def validate_filename(filename: str) -> bool:
    """Validate the filename to ensure it's safe to use"""
    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    if any(char in filename for char in invalid_chars):
        print(f"✗ Invalid filename: contains invalid characters ({invalid_chars})")
        return False
    return True

def main():
    """Main function to generate audio files based on command line arguments"""
    parser = argparse.ArgumentParser(description='Generate Japanese TTS audio files')
    parser.add_argument('--text', required=True, help='Japanese text to convert to speech')
    parser.add_argument('--filename', required=True, help='Output filename (without extension)')
    parser.add_argument('--voice', choices=['male', 'female'], help='Voice to use (male or female)')
    
    args = parser.parse_args()

    print("Japanese TTS Audio Generator")
    print("=" * 40)

    # Validate filename
    if not validate_filename(args.filename):
        return

    # Check if TTS service is available
    if not check_tts_service():
        return

    # Create output directory
    create_output_directory()

    # Generate audio
    success = generate_tts_audio(
        text=args.text,
        filename=args.filename,
        voice_id=args.voice
    )

    # Summary
    print("\n" + "=" * 40)
    if success:
        print(f"\n✓ Audio file has been saved to the '{OUTPUT_DIR}' directory:")
        print(f"  - {args.filename}.mp3 (or .wav)")
    else:
        print("\n⚠ File generation failed. Check the error messages above.")

    print("\nNote: If MP3 conversion failed, WAV file was kept instead.")
    print("You can convert it manually using: ffmpeg -i input.wav -codec:a libmp3lame output.mp3")

if __name__ == "__main__":
    main()
