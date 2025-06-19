import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional, Dict, List, Union
import os
from backend.config import ServiceConfig
from backend.utils.helper import get_file_path
from backend.image.llm_client import LLMClient

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
        
        # Initialize LLM client for translations
        self.llm_client = LLMClient()

    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response from LLM for translations"""
        try:
            response = self.session.post(
                f"{ServiceConfig.OLLAMA_URL}/api/chat",
                json={
                    "model": ServiceConfig.OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional Japanese to English translator. Translate the given Japanese text to English, maintaining the original meaning and context. Do not add any explanations, notes, or alternative translations. Only provide the direct translation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False
                },
                timeout=ServiceConfig.get_timeout("ollama")
            )
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return ""

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
            if any(ord(c) > 0x4e00 for c in prompt):
                logger.info("Translating Japanese prompt to English")
                translated_prompt = self.llm_client.generate_response(f"Translate this Japanese text to English: {prompt}")
                logger.info(f"Translated prompt: {translated_prompt}")
            else:
                translated_prompt = prompt

            # Use waifu-diffusion for image generation
            endpoint = ServiceConfig.get_endpoint("vision", "generate")
            if not endpoint:
                logger.error("Waifu-diffusion generate endpoint not configured")
                return None

            logger.info(f"Sending image generation request to {endpoint} with prompt: {translated_prompt}")
            response = self.session.post(
                endpoint,
                json={
                    "prompt": translated_prompt,
                    "style": style,
                    "return_format": "base64"  # Request base64 format for easier handling
                },
                timeout=ServiceConfig.get_timeout("waifu-diffusion")
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            if "image" in result:
                # Convert base64 to bytes
                import base64
                image_data = base64.b64decode(result["image"])
                logger.info("Successfully generated and decoded image")
                return image_data
            else:
                logger.error(f"Unexpected response format: {result}")
                return None

        except requests.exceptions.Timeout:
            logger.error("Image generation timed out - this is normal when running on CPU")
            return None
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
            # Verify the file was created and has content
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"Successfully saved image to {filepath}")
                return True
            else:
                logger.error(f"File was not created or is empty: {filepath}")
                return False
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

    def generate_option_images(self, prompts: dict, base_filename: str) -> dict:
        """
        Generate images for all options.
        
        Args:
            prompts (dict): Dictionary of prompts keyed by option letter (A, B, C, D)
            base_filename (str): Base filename for the images
            
        Returns:
            dict: Dictionary of image paths keyed by option letter
        """
        image_paths = {}
        
        # Get the images directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        images_dir = os.path.join(project_root, "backend", "data", "images")
        
        # Ensure images directory exists
        os.makedirs(images_dir, exist_ok=True)
        
        for option_letter, prompt in prompts.items():
            try:
                # Generate image
                image_data = self.generate_image(prompt, style="anime")
                if image_data:
                    # Create filename for this option
                    filename = f"{base_filename}_option_{option_letter}.png"
                    # Create full path
                    full_path = os.path.join(images_dir, filename)
                    # Save image
                    if self.save_image(image_data, full_path):
                        # Store only the relative path in the dictionary
                        image_paths[option_letter] = filename
                        logger.info(f"Successfully generated and saved image for option {option_letter}")
                    else:
                        logger.error(f"Failed to save image for option {option_letter}")
                else:
                    logger.error(f"Failed to generate image for option {option_letter}")
            except Exception as e:
                logger.error(f"Error processing option {option_letter}: {str(e)}")
                continue
        
        return image_paths
