"""
OCR module for processing Japanese text from images.
"""
import logging
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import requests
from ..utils.config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)

class OCRProcessor:
    """Handles OCR processing of Japanese text from images via MangaOCR API."""
    
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or get_config().get('mangaocr_endpoint', 'http://localhost:9000/analyze')
    
    def process_image(
        self,
        image: Union[str, Path, Image.Image],
        save_temp: bool = False
    ) -> Optional[str]:
        """
        Process an image to extract Japanese text using MangaOCR API.
        Args:
            image: Image to process (file path or PIL Image)
            save_temp: Whether to save temporary files for debugging
        Returns:
            Extracted text or None if processing failed
        """
        temp_path = None
        try:
            # Convert to PIL Image if needed
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            # Save to temporary file
            temp_path = Path(get_config()['temp_dir']) / "ocr_temp.png"
            image.save(temp_path)
            with open(temp_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(self.endpoint, files=files, timeout=30)
            if temp_path.exists():
                temp_path.unlink()
            if response.status_code == 200:
                return response.json().get('text')
            else:
                logger.error(f"MangaOCR API error: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            if temp_path and temp_path.exists():
                temp_path.unlink()
            return None
    def is_available(self) -> bool:
        """Check if OCR API is available (always True if endpoint is set)."""
        return self.endpoint is not None

# Create singleton instance
_ocr_processor = None

def get_ocr_processor() -> OCRProcessor:
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor 