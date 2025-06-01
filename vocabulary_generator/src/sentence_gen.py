from typing import List, Dict
import requests

class SentenceGenerator:
    def __init__(self, ollama_endpoint: str):
        self.endpoint = ollama_endpoint

    async def generate_examples(self, word: str, level: str = "N5", num_sentences: int = 2) -> List[Dict[str, str]]:
        """Generate example sentences for a given word"""
        prompt = f"""
        Generate {num_sentences} simple Japanese sentences using the word "{word}".
        Requirements:
        - Use only JLPT {level} level grammar and vocabulary
        - Each sentence should be 5-7 words long
        - Include natural particle usage
        - Provide English translations
        Format: Return as JSON array with "japanese" and "english" keys
        """

        response = requests.post(
            self.endpoint,
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )

        if response.status_code == 200:
            return response.json()["message"]["content"]
        else:
            raise Exception(f"Failed to generate sentences: {response.status_code}")

    async def validate_sentence_level(self, sentence: str, level: str = "N5") -> bool:
        """Verify if a sentence uses appropriate level vocabulary and grammar"""
        prompt = (
            f"Does the following Japanese sentence use only JLPT {level} grammar and vocabulary? "
            f"Answer 'yes' or 'no'. Sentence: {sentence}"
        )
        response = requests.post(
            self.endpoint,
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
        )
        if response.status_code == 200:
            answer = response.json()["message"]["content"].strip().lower()
            return answer.startswith("yes")
        else:
            raise Exception(f"Failed to validate sentence: {response.status_code}")