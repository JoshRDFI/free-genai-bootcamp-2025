# Vision service integration

import requests
import json
import base64
import os

class VisionService:
    """Service for interacting with the image generation service"""
    
    def __init__(self, base_url=None):
        # Use the direct waifu-diffusion service URL
        self.image_gen_url = base_url or os.environ.get('WAIFU_DIFFUSION_URL', 'http://localhost:9500')
        
    def generate_image(self, prompt, style="anime", width=512, height=512):
        """Generate image based on prompt"""
        try:
            response = requests.post(
                f"{self.image_gen_url}",
                json={
                    "prompt": prompt,
                    "style": style,
                    "width": width,
                    "height": height
                },
                timeout=60  # Image generation can take time
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling image generation service: {e}")
            return {"error": str(e)}
    
    def generate_character(self, description, outfit="casual", emotion="neutral"):
        """Generate character image based on description"""
        try:
            response = requests.post(
                f"{self.image_gen_url}/character",
                json={
                    "description": description,
                    "outfit": outfit,
                    "emotion": emotion,
                    "style": "anime"
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling image generation service: {e}")
            return {"error": str(e)}