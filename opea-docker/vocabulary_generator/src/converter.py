import pykakasi
from typing import Dict, List

class JapaneseConverter:
    def __init__(self):
        self.kakasi = pykakasi.kakasi()
        self.kakasi.setMode("H", "a")  # Hiragana to ascii
        self.kakasi.setMode("K", "a")  # Katakana to ascii
        self.kakasi.setMode("J", "a")  # Kanji to ascii
        self.converter = self.kakasi.getConverter()

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