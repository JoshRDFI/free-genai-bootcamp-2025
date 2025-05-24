import json
import logging
from typing import Dict, Optional, Union
import requests
from pathlib import Path
import pykakasi
from typing import Dict, List

logger = logging.getLogger(__name__)

class JapaneseConverter:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.mangaocr_endpoint = self.config['vision_services']['mangaocr']['endpoint']
        self.llava_endpoint = self.config['vision_services']['llava']['endpoint']
        self.kakasi = pykakasi.kakasi()
        self.kakasi.setMode("H", "a")  # Hiragana to ascii
        self.kakasi.setMode("K", "a")  # Katakana to ascii
        self.kakasi.setMode("J", "a")  # Kanji to ascii
        self.converter = self.kakasi.getConverter()

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """
        Extract Japanese text from an image using MangaOCR.
        
        Args:
            image_data (bytes): The image data to process
            
        Returns:
            Optional[str]: The extracted Japanese text, or None if extraction failed
        """
        try:
            files = {'image': ('image.jpg', image_data, 'image/jpeg')}
            response = requests.post(
                self.mangaocr_endpoint,
                files=files,
                timeout=self.config['vision_services']['mangaocr']['timeout']
            )
            response.raise_for_status()
            return response.json().get('text')
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return None

    async def analyze_image_content(self, image_data: bytes) -> Optional[Dict]:
        """
        Analyze image content using LLaVA.
        
        Args:
            image_data (bytes): The image data to analyze
            
        Returns:
            Optional[Dict]: Analysis results including detected text and context
        """
        try:
            files = {'image': ('image.jpg', image_data, 'image/jpeg')}
            response = requests.post(
                self.llava_endpoint,
                files=files,
                timeout=self.config['vision_services']['llava']['timeout']
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error analyzing image content: {str(e)}")
            return None

    async def process_image(self, image_data: bytes) -> Dict:
        """
        Process an image to extract both Japanese text and analyze its content.
        
        Args:
            image_data (bytes): The image data to process
            
        Returns:
            Dict: Combined results from both MangaOCR and LLaVA analysis
        """
        text_result = await self.extract_text_from_image(image_data)
        content_result = await self.analyze_image_content(image_data)
        
        return {
            'extracted_text': text_result,
            'content_analysis': content_result
        }

    def convert_to_romaji(self, text: str) -> str:
        """
        Convert Japanese text to romaji.
        This is a placeholder for actual romaji conversion logic.
        """
        # TODO: Implement actual romaji conversion
        return text

    def convert_to_hiragana(self, text: str) -> str:
        """
        Convert Japanese text to hiragana.
        This is a placeholder for actual hiragana conversion logic.
        """
        # TODO: Implement actual hiragana conversion
        return text

    def to_romaji(self, text: str) -> str:
        """Convert Japanese text to romaji"""
        return self.converter.do(text)

    def parse_word_parts(self, word: str) -> List[Dict[str, List[str]]]:
        """Break down a word into its component parts with readings"""
        result = []
        conv = self.kakasi.convert(word)

        for part in conv:
            result.append({
                "kanji": part['orig'],
                "romaji": [part['hepburn']]
            })
        return result

    def validate_romaji(self, kanji: str, romaji: str) -> bool:
        """Verify if the provided romaji matches the kanji"""
        generated_romaji = self.to_romaji(kanji)
        return generated_romaji.lower() == romaji.lower()