# backend/llm/chat.py
import os
import requests
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
from backend.config import ServiceConfig
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "chat_interface.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self):
        """Initialize chat interface with retry mechanism"""
        self.endpoint = ServiceConfig.LLM_TEXT_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=ServiceConfig.RETRY_CONFIG["max_retries"],
            backoff_factor=ServiceConfig.RETRY_CONFIG["backoff_factor"],
            status_forcelist=ServiceConfig.RETRY_CONFIG["status_forcelist"]
        )
        
        # Create session with retry strategy
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        logger.info(f"Initialized ChatInterface with endpoint: {self.endpoint}")

    def generate_questions(self, transcript_text: str, num_questions: int = 3) -> List[Dict]:
        """Generate questions from transcript using LLM."""
        try:
            logger.info(f"Starting question generation for {num_questions} questions")
            
            # Prepare the prompt
            prompt = f"""Generate {num_questions} multiple-choice questions in Japanese based on this transcript:
            {transcript_text}
            
            Each question should have:
            1. A clear question in Japanese
            2. 4 options in Japanese
            3. The correct answer (1-4)
            
            Format each question as a JSON object with these fields:
            - Question: The question text
            - Options: Array of 4 options
            - CorrectAnswer: Number (1-4) of the correct option
            
            Return an array of these JSON objects."""

            # Prepare the request payload
            payload = {
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": "You are a Japanese language teacher creating listening comprehension questions."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # Try the request with retries
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info("Sending request to LLM service")
                    response = self.session.post(
                        self.endpoint,
                        json=payload,
                        headers=self.headers,
                        timeout=ServiceConfig.get_timeout("llm")
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        questions = self._parse_llm_response(result)
                        if questions:
                            logger.info(f"Successfully generated {len(questions)} questions")
                            return questions
                        else:
                            logger.error("Failed to parse LLM response")
                    else:
                        logger.error(f"LLM service returned error status: {response.status_code}")
                        try:
                            error_detail = response.json()
                            logger.error(f"Response content: {error_detail}")
                        except:
                            logger.error(f"Response content: {response.text}")
                            
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise

            raise Exception("Failed to generate questions after all retries")

        except Exception as e:
            logger.error(f"Unexpected error generating questions: {str(e)}")
            raise

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
                json=prompt,
                timeout=ServiceConfig.get_timeout("llm")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
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
                json=prompt,
                timeout=ServiceConfig.get_timeout("llm")
            )
            response.raise_for_status()
            return response.json()["speakers"]
        except Exception as e:
            logger.error(f"Error analyzing conversation: {str(e)}")
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
                json={"text": text},
                timeout=ServiceConfig.get_timeout("llm")
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding in chat: {str(e)}")
            return None

    def _parse_llm_response(self, result: Dict) -> List[Dict]:
        """Parse the LLM response into a list of questions."""
        try:
            if "choices" not in result or not result["choices"]:
                logger.error("No choices in LLM response")
                return []
                
            content = result["choices"][0]["message"]["content"]
            try:
                questions = json.loads(content)
                if not isinstance(questions, list):
                    logger.error("Response is not a list of questions")
                    return []
                    
                # Validate each question
                valid_questions = []
                for q in questions:
                    if all(key in q for key in ["Question", "Options", "CorrectAnswer"]):
                        if isinstance(q["Options"], list) and len(q["Options"]) == 4:
                            if isinstance(q["CorrectAnswer"], int) and 1 <= q["CorrectAnswer"] <= 4:
                                valid_questions.append(q)
                            else:
                                logger.warning("Invalid CorrectAnswer format")
                        else:
                            logger.warning("Invalid Options format")
                    else:
                        logger.warning("Question missing required fields")
                        
                return valid_questions
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse questions JSON: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return []