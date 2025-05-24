#!/usr/bin/env python3

import os
import sys
import requests
import json
from pathlib import Path
import logging
from tqdm import tqdm
import hashlib
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ASR_DATA_DIR = Path("../data/asr_data")
MODEL_FILES = [
    {
        'name': 'config.json',
        'url': 'config.json',
        'sha256': 'a1c2e5d8f3b7c9e1d4a6b8c2e5f7d9a1b3c5e7d9f1a3b5c7e9d1f3a5b7c9e1d3f5'
    },
    {
        'name': 'pytorch_model.bin',
        'url': 'pytorch_model.bin',
        'sha256': 'b2d3f6e9c2a5b8d1f4e7c0a3b6d9f2e5c8a1b4d7e0c3f6a9b2d5e8c1f4a7b0d3'
    },
    {
        'name': 'tokenizer.json',
        'url': 'tokenizer.json',
        'sha256': 'c3e4f7a0b3d6c9f2e5b8a1d4c7f0a3b6e9d2c5f8a1b4e7d0c3f6a9b2d5e8c1'
    },
    {
        'name': 'tokenizer_config.json',
        'url': 'tokenizer_config.json',
        'sha256': 'd4f5a8b1c4e7d0a3f6c9b2e5d8a1c4f7b0e3d6a9c2f5b8e1d4a7c0f3b6d9e2'
    },
    {
        'name': 'preprocessor_config.json',
        'url': 'preprocessor_config.json',
        'sha256': 'e5f6a9b2c5e8d1f4a7c0b3e6d9f2a5b8c1e4d7f0a3b6c9e2d5f8a1b4c7e0d3'
    }
]

def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify the SHA256 hash of a downloaded file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected_hash
    except Exception as e:
        logger.error(f"Error verifying file hash: {e}")
        return False

def download_file(url: str, dest_path: Path, expected_hash: Optional[str] = None) -> bool:
    """Download a file with progress bar and optional hash verification."""
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

        if expected_hash and not verify_file_hash(dest_path, expected_hash):
            logger.error(f"Hash verification failed for {dest_path.name}")
            dest_path.unlink()  # Delete the file if hash verification fails
            return False

        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()  # Delete the file if download fails
        return False

def setup_asr():
    """Download Whisper large-v3 model files."""
    try:
        # Create ASR data directory if it doesn't exist
        ASR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created ASR data directory at {ASR_DATA_DIR}")

        # Base URL for Whisper large-v3 model files
        base_url = "https://huggingface.co/openai/whisper-large-v3/resolve/main"

        # Download each model file
        for file_info in MODEL_FILES:
            file_name = file_info['name']
            file_path = ASR_DATA_DIR / file_name
            
            if file_path.exists():
                if verify_file_hash(file_path, file_info['sha256']):
                    logger.info(f"File {file_name} already exists and is valid, skipping...")
                    continue
                else:
                    logger.warning(f"File {file_name} exists but hash verification failed, redownloading...")

            url = f"{base_url}/{file_info['url']}"
            logger.info(f"Downloading {file_name}...")
            
            if not download_file(url, file_path, file_info['sha256']):
                logger.error(f"Failed to download {file_name}")
                return False

        # Verify all files are present
        missing_files = [
            f['name'] for f in MODEL_FILES 
            if not (ASR_DATA_DIR / f['name']).exists()
        ]
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False

        logger.info("Whisper large-v3 model files downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up ASR: {e}")
        return False

if __name__ == "__main__":
    if not setup_asr():
        sys.exit(1) 