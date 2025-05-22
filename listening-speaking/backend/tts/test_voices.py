#!/usr/bin/env python3

import os
import sys
import logging
from tts_engine import TTSEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_voices():
    """Test both male and female voices."""
    tts = TTSEngine()
    
    # Test text in Japanese
    test_text = "こんにちは、これはテストです。"
    
    # Get available voices
    logger.info("Checking available voices...")
    voices = tts.get_available_voices()
    logger.info(f"Available voices: {voices}")
    
    # Create output directory if it doesn't exist
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test male voice
    logger.info("Testing male voice...")
    male_audio = tts.synthesize_speech(
        text=test_text,
        voice_id="male_voice.wav",
        language="ja"
    )
    if male_audio:
        male_output = os.path.join(output_dir, "test_male.wav")
        if tts.save_audio(male_audio, male_output):
            logger.info(f"Male voice test successful. Output saved to: {male_output}")
        else:
            logger.error("Failed to save male voice test output")
    else:
        logger.error("Failed to generate male voice")
    
    # Test female voice
    logger.info("Testing female voice...")
    female_audio = tts.synthesize_speech(
        text=test_text,
        voice_id="female_voice.wav",
        language="ja"
    )
    if female_audio:
        female_output = os.path.join(output_dir, "test_female.wav")
        if tts.save_audio(female_audio, female_output):
            logger.info(f"Female voice test successful. Output saved to: {female_output}")
        else:
            logger.error("Failed to save female voice test output")
    else:
        logger.error("Failed to generate female voice")

if __name__ == "__main__":
    try:
        test_voices()
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1) 