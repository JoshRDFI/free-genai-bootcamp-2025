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
        # Test connection to endpoint
        try:
            response = requests.get(f"{endpoint}/health")
            if response.status_code != 200:
                logger.error(f"LLM service health check failed with status {response.status_code}")
            else:
                logger.info("Successfully connected to LLM service")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to LLM service at {endpoint}: {str(e)}")
        logger.info(f"Initialized ChatInterface with endpoint: {endpoint}")

    def generate_questions(self, transcript: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate listening comprehension questions from transcript.
        """
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
            # Try to connect with timeout
            response = requests.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=self.headers,
                json=prompt,
                timeout=30  # Add timeout
            )
            logger.info(f"Received response with status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"LLM service returned error status: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return []
                
            try:
                result = response.json()
                logger.info("Successfully parsed response JSON")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Raw response: {response.text}")
                return []
            
            # Parse the response content as JSON
            try:
                if "message" not in result:
                    logger.error(f"Unexpected response format - missing 'message': {result}")
                    return []
                    
                content = result["message"]["content"]
                logger.info("Successfully extracted content from response")
                
                questions_data = json.loads(content)
                logger.info("Successfully parsed questions data")
                
                if "questions" in questions_data:
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
                    
                    if valid_questions:
                        return valid_questions
                    else:
                        logger.error("No valid questions found in response")
                        return []
                else:
                    logger.error(f"Response missing 'questions' key: {questions_data}")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM response content as JSON: {str(e)}")
                logger.error(f"Raw content: {content}")
                return []
            except Exception as e:
                logger.error(f"Error processing questions data: {str(e)}", exc_info=True)
                return []
        except requests.exceptions.Timeout:
            logger.error("Request to LLM service timed out")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to LLM service at {self.endpoint}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating questions: {str(e)}", exc_info=True)
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