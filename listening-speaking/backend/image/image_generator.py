import requests
import os
from backend.utils.helper import get_file_path

class ImageGenerator:
    def __init__(self, model_name: str = "lineart-sd"):
        """Initialize the image generator with LineArt SD"""
        self.model_name = model_name

    def generate_image(self, prompt: str, filename: str) -> str:
        """Generate a line art image using local model"""
        try:
            # Configuration for line art generation
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "parameters": {
                    "width": 400,
                    "height": 400,
                    "steps": 20,
                    "guidance_scale": 7.5,
                    "negative_prompt": "color, shading, complex, detailed, noise, texture",
                    "sampler": "euler_a",
                    "style_preset": "line-art"
                }
            }

            # Call local model through Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload
            )

            if response.status_code == 200:
                image_data = response.content
                file_path = get_file_path("data/images", filename, "png")
                with open(file_path, "wb") as f:
                    f.write(image_data)
                return file_path
            else:
                raise Exception(f"Image generation failed: {response.text}")
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None
