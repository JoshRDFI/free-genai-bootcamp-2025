# backend/llm/chat.py

import requests
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
from backend.config import ServiceConfig
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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
        
        # Test connection to endpoint
        try:
            response = self.session.get(f"{self.endpoint}/health", timeout=5)
            if response.status_code != 200:
                logger.error(f"LLM service health check failed with status {response.status_code}")
            else:
                logger.info("Successfully connected to LLM service")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to LLM service at {self.endpoint}: {str(e)}")
        logger.info(f"Initialized ChatInterface with endpoint: {self.endpoint}")

    def generate_questions(self, transcript: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate listening comprehension questions from transcript.
        """
        if not transcript.strip():
            logger.error("Empty transcript provided")
            raise ValueError("Empty transcript provided")
            
        if num_questions < 1:
            logger.error("Invalid number of questions requested")
            raise ValueError("Invalid number of questions requested")
            
        logger.info(f"Starting question generation for {num_questions} questions")
        
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
            response = self.session.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=self.headers,
                json=prompt,
                timeout=ServiceConfig.get_timeout("llm")
            )
            
            logger.info(f"Received response with status code: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text if response.text else "No error details available"
                logger.error(f"LLM service returned error status: {response.status_code}")
                logger.error(f"Response content: {error_detail}")
                raise Exception(f"LLM service error: {response.status_code} - {error_detail}")
                
            try:
                result = response.json()
                logger.info("Successfully parsed response JSON")
                
                # Handle both possible response formats
                if "response" in result:  # Ollama format
                    content = result["response"]
                elif "message" in result and "content" in result["message"]:  # OpenAI format
                    content = result["message"]["content"]
                else:
                    logger.error(f"Unexpected response format: {result}")
                    raise ValueError(f"Unexpected response format from LLM service")
                
                # Parse the content as JSON
                try:
                    questions_data = json.loads(content)
                    logger.info("Successfully parsed questions data")
                    
                    if "questions" not in questions_data:
                        logger.error(f"Response missing 'questions' key: {questions_data}")
                        raise ValueError("Response missing 'questions' key")
                        
                    questions = questions_data["questions"]
                    logger.info(f"Successfully extracted {len(questions)} questions")
                    
                    # Validate question format
                    valid_questions = []
                    for i, q in enumerate(questions):
                        if all(key in q for key in ["Introduction", "Conversation", "Question", "Options"]):
                            if isinstance(q["Options"], list) and len(q["Options"]) == 4:
                                valid_questions.append(q)
                            else:
                                logger.warning(f"Question {i+1} has invalid options format")
                        else:
                            logger.warning(f"Question {i+1} is missing required fields")
                    
                    if not valid_questions:
                        logger.error("No valid questions found in response")
                        raise ValueError("No valid questions found in LLM response")
                        
                    return valid_questions
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing LLM response content as JSON: {str(e)}")
                    logger.error(f"Raw content: {content}")
                    raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Raw response: {response.text}")
                raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
                
        except requests.exceptions.Timeout:
            logger.error("Request to LLM service timed out")
            raise TimeoutError("LLM service request timed out")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to LLM service at {self.endpoint}")
            raise ConnectionError(f"Failed to connect to LLM service at {self.endpoint}")
            
        except Exception as e:
            logger.error(f"Unexpected error generating questions: {str(e)}", exc_info=True)
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