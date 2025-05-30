#!/usr/bin/env python3

import os
import sys
import requests
import json
from pathlib import Path
import logging
from tqdm import tqdm
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
WAIFU_DATA_DIR = Path("../data/waifu")
MODEL_FILES = [
    'model_index.json',
    'feature_extractor/preprocessor_config.json',
    'safety_checker/config.json',
    'safety_checker/pytorch_model.bin',
    'scheduler/scheduler_config.json',
    'text_encoder/config.json',
    'text_encoder/pytorch_model.bin',
    'tokenizer/vocab.json',
    'tokenizer/merges.txt',
    'tokenizer/special_tokens_map.json',
    'tokenizer/tokenizer_config.json',
    'unet/config.json',
    'unet/diffusion_pytorch_model.bin',
    'vae/config.json',
    'vae/diffusion_pytorch_model.bin'
]

def download_file(url: str, dest_path: Path) -> bool:
    """Download a file with progress bar."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=8192):
                size = f.write(data)
                pbar.update(size)

        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()  # Delete the file if download fails
        return False

def setup_waifu():
    """Download waifu-diffusion model files."""
    try:
        # Create waifu data directory if it doesn't exist
        WAIFU_DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created waifu data directory at {WAIFU_DATA_DIR}")

        # Base URL for waifu-diffusion model files
        base_url = "https://huggingface.co/hakurei/waifu-diffusion/raw/main"

        # Download each model file
        for file_name in MODEL_FILES:
            file_path = WAIFU_DATA_DIR / file_name
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.exists():
                logger.info(f"File {file_name} already exists, skipping...")
                continue

            url = f"{base_url}/{file_name}"
            logger.info(f"Downloading {file_name}...")
            
            if not download_file(url, file_path):
                logger.error(f"Failed to download {file_name}")
                return False

        # Verify all files are present
        missing_files = [
            f for f in MODEL_FILES 
            if not (WAIFU_DATA_DIR / f).exists()
        ]
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False

        logger.info("Waifu-diffusion model files downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up waifu-diffusion: {e}")
        return False

if __name__ == "__main__":
    if not setup_waifu():
        sys.exit(1) 