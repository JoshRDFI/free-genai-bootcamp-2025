#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
from pathlib import Path
# from transformers import AutoProcessor, AutoModelForCausalLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VISION_DATA_DIR = Path("../data/llm_vision_data")
MODEL_ID = "llava-hf/llava-1.5-7b-hf"

def install_requirements():
    """Install required packages for LLaVA."""
    try:
        logger.info("Installing required packages...")
        # Install transformers and other requirements not in base.txt
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "transformers>=4.35.3",
            "accelerate",
            "packaging<25.0"  # Fix streamlit dependency conflict
        ])
        logger.info("Required packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing requirements: {e}")
        return False

def setup_vision():
    """Download LLaVA-1.5-7B model files using Hugging Face transformers."""
    try:
        # Install required packages first
        if not install_requirements():
            return False
        from transformers import AutoModelForVision2Seq, AutoProcessor
        print("transformers imported")
        
        # Create vision data directory if it doesn't exist
        VISION_DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created vision data directory at {VISION_DATA_DIR}")

        # Download model and processor
        logger.info(f"Downloading LLaVA model from {MODEL_ID}...")
        model = AutoModelForVision2Seq.from_pretrained(
            MODEL_ID,
            cache_dir=VISION_DATA_DIR,
            local_files_only=False,
            trust_remote_code=True,  # Required for LLaVA models
            torch_dtype="auto",  # Automatically select the best dtype for your GPU
            device_map="auto"  # Automatically handle device placement
        )
        processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            cache_dir=VISION_DATA_DIR,
            local_files_only=False,
            trust_remote_code=True  # Required for LLaVA models
        )

        logger.info("LLaVA-1.5-7B model files downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up vision model: {e}")
        return False

if __name__ == "__main__":
    if not setup_vision():
        sys.exit(1) 