#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_asr():
    """Download Whisper large-v3 model files using Hugging Face transformers."""
    try:
        # Create ASR data directory if it doesn't exist
        asr_data_dir = Path("../data/asr_data")
        asr_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created ASR data directory at {asr_data_dir}")

        # Set the cache directory to our data directory
        os.environ['TRANSFORMERS_CACHE'] = str(asr_data_dir)

        # Download model and processor
        logger.info("Downloading Whisper large-v3 model and processor...")
        model = WhisperForConditionalGeneration.from_pretrained('whisper-large-v3')
        processor = WhisperProcessor.from_pretrained('whisper-large-v3')

        # Save them explicitly to our data directory
        logger.info("Saving model and processor to data directory...")
        model.save_pretrained(str(asr_data_dir))
        processor.save_pretrained(str(asr_data_dir))

        logger.info("Whisper large-v3 model files downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up ASR: {e}")
        return False

if __name__ == "__main__":
    if not setup_asr():
        sys.exit(1) 