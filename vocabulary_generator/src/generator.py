# src/generator.py
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VocabularyGenerator:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.ollama_endpoint = self.config['api']['ollama_endpoint']
        self.mangaocr_endpoint = self.config['vision_services']['mangaocr']['endpoint']
        self.llava_endpoint = self.config['vision_services']['llava']['endpoint']
        
        # Create image output directory if it doesn't exist
        self.image_output_dir = Path(self.config['storage']['image_output_dir'])
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def generate_vocabulary_entry(self, word: str, level: str = "N5", include_image: bool = False) -> Dict:
        """Generate a complete vocabulary entry including examples and validations"""
        prompt = self._create_vocabulary_prompt(word, level)

        response = requests.post(
            self.ollama_endpoint,
            json={
                "model": "llama3.2",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
            }
        )

        if response.status_code == 200:
            entry = response.json()["message"]["content"]
            validated_entry = self.validate_entry(entry, level)
            
            if include_image:
                # Generate visual example using LLaVA
                image_data = await self.generate_visual_example(word, level)
                if image_data:
                    image_path = self._save_image(image_data, word)
                    validated_entry['visual_example'] = image_path
            
            return validated_entry
        else:
            raise Exception(f"Failed to generate entry: {response.status_code}")

    async def extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """Extract Japanese text from an image using MangaOCR"""
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
        """Analyze image content using LLaVA"""
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

    async def generate_visual_example(self, word: str, level: str) -> Optional[bytes]:
        """Generate a visual example for the vocabulary word using LLaVA"""
        try:
            prompt = f"Create a visual representation of the Japanese word '{word}' at JLPT {level} level"
            response = requests.post(
                self.llava_endpoint,
                json={
                    "prompt": prompt,
                    "style": "educational"
                },
                timeout=self.config['vision_services']['llava']['timeout']
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error generating visual example: {str(e)}")
            return None

    def _save_image(self, image_data: bytes, word: str) -> str:
        """Save image data to file and return the path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{word.replace('/', '_')}_{timestamp}.jpg"
        filepath = self.image_output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return str(filepath)

    def _create_vocabulary_prompt(self, word: str, level: str) -> str:
        return f"""
        Create a Japanese vocabulary entry for the word "{word}" at JLPT {level} level.
        Include:
        1. Kanji form
        2. Romaji reading
        3. English meaning
        4. Word parts breakdown
        5. Two example sentences (both in Japanese and English)
        Format the response as a JSON object.
        """

    def validate_entry(self, entry: Dict, level: str) -> Dict:
        # Implement JLPT level validation
        # This will be expanded in the validator module
        pass

    async def save_entry(self, entry: Dict, group_name: str) -> None:
        """Save entry to both JSON file and database"""
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = f"data/json_output/{group_name}_{timestamp}.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        # Save to database (to be implemented)
        await self._save_to_database(entry, group_name)

    async def _save_to_database(self, entry: Dict, group_name: str) -> None:
        # Database operations will be implemented in database.py
        pass

    async def import_from_json(self, json_path: str) -> List[Dict]:
        """Import vocabulary entries from existing JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        validated_entries = []
        for entry in entries:
            validated_entry = self.validate_entry(entry, "N5")
            if validated_entry:
                validated_entries.append(validated_entry)

        return validated_entries

    async def generate_example_sentences(self, word: str, num_sentences: int = 2) -> List[str]:
        """Generate example sentences using the word"""
        prompt = f"""
        Generate {num_sentences} example sentences in Japanese using the word "{word}".
        Each sentence should be appropriate for JLPT N5 level.
        Include English translations.
        """

        # Implementation will use the ollama-server
        pass