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

class ModelSetup:
    def __init__(
        self,
        service_name: str,
        model_files: List[Dict[str, str]],
        base_url: str,
        data_dir: Optional[str] = None
    ):
        """
        Initialize the model setup.
        
        Args:
            service_name: Name of the service (e.g., 'tts', 'asr', 'vision')
            model_files: List of dictionaries containing file info:
                       [{'name': 'model.pth', 'url': 'path/to/model.pth', 'sha256': 'hash'}]
            base_url: Base URL for downloading files
            data_dir: Optional custom data directory path
        """
        self.service_name = service_name
        self.model_files = model_files
        self.base_url = base_url
        self.data_dir = Path(data_dir) if data_dir else Path(f"../data/{service_name}_data")

    def verify_file_hash(self, file_path: Path, expected_hash: str) -> bool:
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

    def download_file(self, url: str, dest_path: Path, expected_hash: Optional[str] = None) -> bool:
        """
        Download a file with progress bar and optional hash verification.
        
        Args:
            url: URL to download from
            dest_path: Path to save the file
            expected_hash: Optional SHA256 hash to verify the download
        """
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

            if expected_hash and not self.verify_file_hash(dest_path, expected_hash):
                logger.error(f"Hash verification failed for {dest_path.name}")
                dest_path.unlink()  # Delete the file if hash verification fails
                return False

            return True
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            if dest_path.exists():
                dest_path.unlink()  # Delete the file if download fails
            return False

    def setup_model(self) -> bool:
        """Download and verify all model files."""
        try:
            # Create data directory if it doesn't exist
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created model data directory at {self.data_dir}")

            # Download each model file
            for file_info in self.model_files:
                file_name = file_info['name']
                file_path = self.data_dir / file_name
                
                if file_path.exists():
                    if 'sha256' in file_info:
                        if self.verify_file_hash(file_path, file_info['sha256']):
                            logger.info(f"File {file_name} already exists and is valid, skipping...")
                            continue
                        else:
                            logger.warning(f"File {file_name} exists but hash verification failed, redownloading...")
                    else:
                        logger.info(f"File {file_name} already exists, skipping...")
                        continue

                url = f"{self.base_url}/{file_info['url']}"
                logger.info(f"Downloading {file_name}...")
                
                if not self.download_file(url, file_path, file_info.get('sha256')):
                    logger.error(f"Failed to download {file_name}")
                    return False

            # Verify all files are present
            missing_files = [
                f['name'] for f in self.model_files 
                if not (self.data_dir / f['name']).exists()
            ]
            if missing_files:
                logger.error(f"Missing files: {missing_files}")
                return False

            logger.info(f"{self.service_name.upper()} model files downloaded successfully!")
            return True

        except Exception as e:
            logger.error(f"Error setting up {self.service_name} model: {e}")
            return False

def main():
    """Example usage of the ModelSetup class."""
    # Example configuration for a service
    model_files = [
        {
            'name': 'model.pth',
            'url': 'path/to/model.pth',
            'sha256': 'expected_hash_here'  # Optional
        },
        {
            'name': 'config.json',
            'url': 'path/to/config.json'
        }
    ]
    
    setup = ModelSetup(
        service_name='example',
        model_files=model_files,
        base_url='https://huggingface.co/example/model/resolve/main'
    )
    
    if not setup.setup_model():
        sys.exit(1)

if __name__ == "__main__":
    main() 