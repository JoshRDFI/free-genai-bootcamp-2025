from typing import Dict, List, Set
import json
import os

class JLPTValidator:
    def __init__(self, config_path: str = "config/config.json"):
        self.jlpt_levels = self._load_jlpt_levels(config_path)

    def _load_jlpt_levels(self, config_path: str) -> Dict[str, Set[str]]:
        """Load JLPT level word lists from configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return {level: set(words) for level, words in config['jlpt_words'].items()}

    def validate_level(self, word: str, target_level: str = "N5") -> bool:
        """Check if a word belongs to the specified JLPT level"""
        if target_level not in self.jlpt_levels:
            raise ValueError(f"Invalid JLPT level: {target_level}")
        return word in self.jlpt_levels[target_level]

    def suggest_level(self, word: str) -> str:
        """Suggest the appropriate JLPT level for a word"""
        for level in ["N5", "N4", "N3", "N2", "N1"]:
            if word in self.jlpt_levels[level]:
                return level
        return "Unknown"

    def validate_entry(self, entry: Dict, required_level: str = "N5") -> Dict:
        """Validate a complete vocabulary entry"""
        if not self.validate_level(entry['kanji'], required_level):
            raise ValueError(f"Word '{entry['kanji']}' is not {required_level} level")
        return entry