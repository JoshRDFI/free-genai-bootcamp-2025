#!/usr/bin/env python3

import os
import sys
import requests
import json
from pathlib import Path
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MANGAOCR_DATA_DIR = Path("../data/mangaocr_models")
MODEL_FILES = [
    "config.json",
    "pytorch_model.bin",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.txt"
]

def download_file(url: str, dest_path: Path, chunk_size: int = 8192):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(dest_path, 'wb') as f, tqdm(
        desc=dest_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=chunk_size):
            size = f.write(data)
            pbar.update(size)

def setup_mangaocr():
    """Download MangaOCR model files."""
    try:
        # Create MangaOCR data directory if it doesn't exist
        MANGAOCR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created MangaOCR data directory at {MANGAOCR_DATA_DIR}")

        # Base URL for MangaOCR model files
        base_url = "https://huggingface.co/kha-white/manga-ocr-base/tree/main"

        # Download each model file
        for file_name in MODEL_FILES:
            file_path = MANGAOCR_DATA_DIR / file_name
            if file_path.exists():
                logger.info(f"File {file_name} already exists, skipping...")
                continue

            url = f"{base_url}/{file_name}"
            logger.info(f"Downloading {file_name}...")
            download_file(url, file_path)
            logger.info(f"Downloaded {file_name}")

        # Verify all files are present
        missing_files = [f for f in MODEL_FILES if not (MANGAOCR_DATA_DIR / f).exists()]
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False

        logger.info("MangaOCR model files downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up MangaOCR: {e}")
        return False

if __name__ == "__main__":
    if not setup_mangaocr():
        sys.exit(1) 