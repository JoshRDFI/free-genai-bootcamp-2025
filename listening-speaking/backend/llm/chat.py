# backend/llm/chat.py

import requests
import json
from typing import Dict, Optional, List
from datetime import datetime

class ChatInterface:
    def __init__(self, endpoint: str = "http://localhost:9000"):
        """Initialize chat interface"""
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json"
        }

    def generate_questions(self, transcript: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate listening comprehension questions from transcript.
        """
        prompt = {
            "messages": [{
                "role": "system",
                "content": "You are a JLPT test question generator. Create listening comprehension questions in Japanese."
            }, {
                "role": "user",
                "content": f"""
                Create {num_questions} JLPT-style listening comprehension questions from this transcript:

                {transcript}

                Format each question as:
                - Introduction (situation setup)
                - Conversation (the dialogue)
                - Question (what is being asked)
                - Options (4 possible answers)

                Use natural, conversational Japanese appropriate for the JLPT level.
                """
            }]
        }

        try:
            response = requests.post(
                f"{self.endpoint}/generate",
                headers=self.headers,
                json=prompt
            )
            response.raise_for_status()
            return response.json()["questions"]
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []

    def validate_response(self, question: Dict, selected_answer: int) -> Dict:
        """
        Validate user's answer and provide feedback.
        """
        prompt = {
            "messages": [{
                "role": "system",
                "content": "You are a JLPT test evaluation assistant. Provide feedback on listening comprehension answers."
            }, {
                "role": "user",
                "content": f"""
                Question: {json.dumps(question, ensure_ascii=False)}
                Selected Answer: {selected_answer}

                Evaluate if the answer is correct and provide feedback in Japanese.
                """
            }]
        }

        try:
            response = requests.post(
                f"{self.endpoint}/validate",
                headers=self.headers,
                json=prompt
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error validating response: {str(e)}")
            return {
                "correct": False,
                "feedback": "エラーが発生しました。もう一度お試しください。"
            }

    def get_conversation_roles(self, conversation: str) -> List[Dict]:
        """
        Analyze conversation to determine speaker roles and genders.
        """
        prompt = {
            "messages": [{
                "role": "system",
                "content": "Analyze Japanese conversations to identify speakers and their characteristics."
            }, {
                "role": "user",
                "content": f"""
                Analyze this conversation and identify:
                - Each unique speaker
                - Their role (student, teacher, etc.)
                - Their gender (for voice selection)

                Conversation:
                {conversation}
                """
            }]
        }

        try:
            response = requests.post(
                f"{self.endpoint}/analyze",
                headers=self.headers,
                json=prompt
            )
            response.raise_for_status()
            return response.json()["speakers"]
        except Exception as e:
            print(f"Error analyzing conversation: {str(e)}")
            return []