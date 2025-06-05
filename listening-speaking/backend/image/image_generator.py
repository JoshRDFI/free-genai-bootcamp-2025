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

    def analyze_manga_text(self, image_data: bytes) -> Optional[Dict]:
        """
        Analyze Japanese text in image using MangaOCR service.
        
        Args:
            image_data (bytes): Image data to analyze
            
        Returns:
            Optional[Dict]: Analysis result if successful, None otherwise
        """
        try:
            # Use mangaocr for manga text analysis
            endpoint = ServiceConfig.get_endpoint("vision", "analyze_manga")
            if not endpoint:
                logger.error("MangaOCR analyze endpoint not configured")
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
            logger.error(f"Error analyzing manga text: {str(e)}")
            return None

    def analyze_image_content(self, image_data: bytes) -> Optional[Dict]:
        """
        Analyze image content using LLaVA service.
        
        Args:
            image_data (bytes): Image data to analyze
            
        Returns:
            Optional[Dict]: Analysis result if successful, None otherwise
        """
        try:
            # Use llm-vision for LLaVA image analysis
            endpoint = ServiceConfig.get_endpoint("vision", "analyze_image")
            if not endpoint:
                logger.error("LLaVA analyze endpoint not configured")
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
            logger.error(f"Error analyzing image content: {str(e)}")
            return None

    def generate_image(self, prompt: str, style: str = "anime") -> Optional[bytes]:
        """
        Generate image from prompt using Waifu-diffusion service.
        
        Args:
            prompt (str): Text prompt for image generation
            style (str): Image style (default: anime)
            
        Returns:
            Optional[bytes]: Generated image data if successful, None otherwise
        """
        try:
            # First translate the prompt to English if it's in Japanese
            llm_endpoint = ServiceConfig.get_endpoint("llm_text", "translate")
            if not llm_endpoint:
                logger.error("LLM translate endpoint not configured")
                return None

            # Check if prompt contains Japanese characters
            if any(ord(c) > 0x4e00 for c in prompt):
                logger.info("Translating Japanese prompt to English")
                translation_response = self.session.post(
                    llm_endpoint,
                    json={
                        "text": prompt,
                        "source_lang": "ja",
                        "target_lang": "en"
                    },
                    timeout=ServiceConfig.get_timeout("llm_text")
                )
                translation_response.raise_for_status()
                translated_prompt = translation_response.json().get("translated_text", prompt)
                logger.info(f"Translated prompt: {translated_prompt}")
            else:
                translated_prompt = prompt

            # Use waifu-diffusion for image generation
            endpoint = ServiceConfig.get_endpoint("vision", "generate")
            if not endpoint:
                logger.error("Waifu-diffusion generate endpoint not configured")
                return None

            # Truncate prompt to avoid token length issues
            # Split by commas and take first few items to stay under token limit
            prompt_parts = translated_prompt.split(',')
            truncated_prompt = ','.join(prompt_parts[:3])  # Take first 3 parts
            if len(prompt_parts) > 3:
                logger.warning(f"Prompt truncated from {len(prompt_parts)} to 3 parts")

            logger.info(f"Sending image generation request to {endpoint} with prompt: {truncated_prompt}")
            response = self.session.post(
                endpoint,
                json={
                    "prompt": truncated_prompt,
                    "style": style
                },
                timeout=ServiceConfig.get_timeout("waifu-diffusion")
            )
            response.raise_for_status()
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating image: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                try:
                    logger.error(f"Response content: {e.response.text}")
                except:
                    logger.error("Could not read response content")
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

    def analyze_file(self, filepath: str, analyze_type: str = "content") -> Optional[Dict]:
        """
        Analyze image from file using either MangaOCR or LLaVA service.
        
        Args:
            filepath (str): Path to image file
            analyze_type (str): Type of analysis to perform ("content" for LLaVA or "manga" for MangaOCR)
            
        Returns:
            Optional[Dict]: Analysis result if successful, None otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                image_data = f.read()
            
            if analyze_type == "manga":
                return self.analyze_manga_text(image_data)
            else:
                return self.analyze_image_content(image_data)
        except Exception as e:
            logger.error(f"Error reading image file: {str(e)}")
            return None
