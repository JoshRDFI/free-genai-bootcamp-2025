"""
OCR module for processing Japanese text from images.
"""
import logging
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import manga_ocr
from ..utils.config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)

class OCRProcessor:
    """Handles OCR processing of Japanese text from images."""
    
    def __init__(self):
        """Initialize the OCR processor."""
        self.ocr = None
        self._initialize_ocr()
    
    def _initialize_ocr(self) -> None:
        """Initialize the MangaOCR model."""
        try:
            logger.info("Initializing MangaOCR in CPU mode")
            self.ocr = manga_ocr.MangaOcr()
        except Exception as e:
            logger.error(f"Error initializing MangaOCR: {e}")
            self.ocr = None
    
    def process_image(
        self,
        image: Union[str, Path, Image.Image],
        save_temp: bool = False
    ) -> Optional[str]:
        """
        Process an image to extract Japanese text.
        
        Args:
            image: Image to process (file path or PIL Image)
            save_temp: Whether to save temporary files for debugging
            
        Returns:
            Extracted text or None if processing failed
        """
        if self.ocr is None:
            logger.error("OCR not initialized")
            return None
            
        try:
            # Convert to PIL Image if needed
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            
            # Save to temporary file if requested
            temp_path = None
            if save_temp:
                temp_path = Path(get_config()['temp_dir']) / "ocr_temp.png"
                image.save(temp_path)
                image_path = temp_path
            else:
                # Create temporary file that will be deleted
                temp_path = Path(get_config()['temp_dir']) / "ocr_temp.png"
                image.save(temp_path)
                image_path = temp_path
            
            # Process with OCR
            text = self.ocr(str(image_path))
            
            # Cleanup
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            return text
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            if temp_path and temp_path.exists():
                temp_path.unlink()
            return None
    
    def is_available(self) -> bool:
        """Check if OCR is available."""
        return self.ocr is not None

# Create singleton instance
_ocr_processor = None

def get_ocr_processor() -> OCRProcessor:
    """Get the singleton OCR processor instance."""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor 