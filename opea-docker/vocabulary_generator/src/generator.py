# src/generator.py
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import requests

class VocabularyGenerator:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.ollama_endpoint = "http://localhost:9000/v1/chat/completions"

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def generate_vocabulary_entry(self, word: str, level: str = "N5") -> Dict:
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
            return validated_entry
        else:
            raise Exception(f"Failed to generate entry: {response.status_code}")

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