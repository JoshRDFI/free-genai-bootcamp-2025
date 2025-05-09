import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional, Dict, List, Union
import os
from backend.config import ServiceConfig
from backend.utils.helper import get_file_path

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        """Initialize image generator with retry configuration"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=ServiceConfig.RETRY_CONFIG["max_retries"],
            backoff_factor=ServiceConfig.RETRY_CONFIG["backoff_factor"],
            status_forcelist=ServiceConfig.RETRY_CONFIG["status_forcelist"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def analyze_image(self, image_data: bytes) -> Optional[Dict]:
        """
        Analyze image content using Vision service.
        
        Args:
            image_data (bytes): Image data to analyze
            
        Returns:
            Optional[Dict]: Analysis result if successful, None otherwise
        """
        try:
            endpoint = ServiceConfig.get_endpoint("vision", "analyze")
            if not endpoint:
                logger.error("Vision analyze endpoint not configured")
                return None

            files = {
                'image': ('image.jpg', image_data, 'image/jpeg')
            }

            response = self.session.post(
                endpoint,
                files=files,
                timeout=ServiceConfig.get_timeout("vision")
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return None

    def generate_image(self, prompt: str, style: str = "anime") -> Optional[bytes]:
        """
        Generate image from prompt using Vision service.
        
        Args:
            prompt (str): Text prompt for image generation
            style (str): Image style (default: anime)
            
        Returns:
            Optional[bytes]: Generated image data if successful, None otherwise
        """
        try:
            endpoint = ServiceConfig.get_endpoint("vision", "generate")
            if not endpoint:
                logger.error("Vision generate endpoint not configured")
                return None

            response = self.session.post(
                endpoint,
                json={
                    "prompt": prompt,
                    "style": style
                },
                timeout=ServiceConfig.get_timeout("vision")
            )
            response.raise_for_status()
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating image: {str(e)}")
            return None

    def save_image(self, image_data: bytes, filepath: str) -> bool:
        """
        Save image data to file.
        
        Args:
            image_data (bytes): Image data to save
            filepath (str): Path to save the image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            return True
        except Exception as e:
            logger.error(f"Error saving image file: {str(e)}")
            return False

    def analyze_file(self, filepath: str) -> Optional[Dict]:
        """
        Analyze image from file using Vision service.
        
        Args:
            filepath (str): Path to image file
            
        Returns:
            Optional[Dict]: Analysis result if successful, None otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                image_data = f.read()
            return self.analyze_image(image_data)
        except Exception as e:
            logger.error(f"Error reading image file: {str(e)}")
            return None
