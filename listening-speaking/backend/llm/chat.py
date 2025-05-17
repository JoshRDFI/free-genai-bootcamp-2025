# backend/llm/chat.py

import requests
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/logs/chat_interface.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self, endpoint: str = "http://localhost:9000"):
        """Initialize chat interface"""
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json"
        }
        logger.info(f"Initialized ChatInterface with endpoint: {endpoint}")

    def generate_questions(self, transcript: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate listening comprehension questions from transcript.
        """
        logger.info(f"Generating {num_questions} questions from transcript")
        
        prompt = {
            "model": "llama3.2",
            "messages": [{
                "role": "system",
                "content": "You are a JLPT test question generator. Create listening comprehension questions in Japanese for JLPT5."
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

Return the questions in this JSON format:
{{
    "questions": [
        {{
            "Introduction": "situation setup text",
            "Conversation": "dialogue text",
            "Question": "question text",
            "Options": ["option1", "option2", "option3", "option4"]
        }}
    ]
}}
                """
            }]
        }

        try:
            logger.info("Sending request to LLM service")
            # Use the llm_text service from Docker
            response = requests.post(
                "http://localhost:9000/v1/chat/completions",
                headers=self.headers,
                json=prompt
            )
            logger.info(f"Received response with status code: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            logger.info("Successfully parsed response JSON")
            
            # Parse the response content as JSON
            try:
                content = result["message"]["content"]
                logger.info(f"Raw LLM response content: {content}")
                
                questions_data = json.loads(content)
                logger.info(f"Parsed questions data: {json.dumps(questions_data, indent=2)}")
                
                if "questions" in questions_data:
                    logger.info(f"Successfully extracted {len(questions_data['questions'])} questions")
                    return questions_data["questions"]
                else:
                    logger.error(f"Unexpected response format: {questions_data}")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM response as JSON: {str(e)}")
                logger.error(f"Raw response: {content}")
                return []
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}", exc_info=True)
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

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding from text via Ollama.
        This is similar to the one in KnowledgeBase, but provided here for chat-specific use.
        """
        try:
            response = requests.post(
                f"{self.endpoint}/embed",
                headers=self.headers,
                json={"text": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Error generating embedding in chat: {str(e)}")
            return None