# backend/llm/question_generator.py

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import json
from backend.llm.chat import ChatInterface
from backend.utils.helper import (
    generate_timestamp,
    get_file_path,
    load_json_file,
    save_json_file
)

# Get the absolute path to the logs directory
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
# Create logs directory if it doesn't exist
os.makedirs(logs_dir, exist_ok=True)
# Create the log file path
log_file = os.path.join(logs_dir, "question_generator.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/logs/question_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuestionGenerator:
    def __init__(self):
        """Initialize the question generator"""
        self.questions_file = get_file_path("data", "stored_questions", "json")

    def format_question(self, raw_text: str, section_num: int) -> Optional[Dict]:
        """Format raw text into a structured question"""
        try:
            lines = raw_text.strip().split('\n')
            question = {}
            current_key = None
            current_value = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("Introduction:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Introduction'
                    current_value = [line.replace("Introduction:", "").strip()]
                elif line.startswith("Conversation:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Conversation'
                    current_value = [line.replace("Conversation:", "").strip()]
                elif line.startswith("Question:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Question'
                    current_value = [line.replace("Question:", "").strip()]
                elif line.startswith("Options:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Options'
                    current_value = []
                elif current_key:
                    current_value.append(line)

            if current_key:
                if current_key == 'Options':
                    question[current_key] = current_value
                else:
                    question[current_key] = ' '.join(current_value)

            return question
        except Exception as e:
            print(f"Error formatting question: {str(e)}")
            return None

    def save_question(self, question: Dict, video_id: str, section_num: int) -> bool:
        """Save question to JSON file and generate text file"""
        try:
            # Generate timestamp for unique identification
            timestamp = generate_timestamp()

            # Load existing questions
            questions = load_json_file(self.questions_file) or {}

            # Add new question
            questions[timestamp] = {
                "question": question,
                "video_id": video_id,
                "section_num": section_num,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save to JSON file
            if not save_json_file(self.questions_file, questions):
                return False

            # Save to text file
            text_file = get_file_path(
                "data/questions",
                f"{video_id}_section{section_num}",
                "txt"
            )

            with open(text_file, 'w', encoding='utf-8') as f:
                f.write("<question>\n")
                for key in ['Introduction', 'Conversation', 'Question']:
                    if key in question:
                        f.write(f"{key}:\n{question[key]}\n\n")
                f.write("</question>\n")

            return True
        except Exception as e:
            print(f"Error saving question: {str(e)}")
            return False

    def generate_questions(self, transcript: List[Dict], video_id: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate questions from transcript using LLM.

        Args:
            transcript (List[Dict]): The transcript data
            video_id (str): The YouTube video ID
            num_questions (int): Number of questions to generate

        Returns:
            List[Dict]: List of generated questions
        """
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("backend/logs", exist_ok=True)

            # Extract text from transcript
            transcript_text = "\n".join(item["text"] for item in transcript)
            logger.info(f"Extracted transcript text for video {video_id}")

            # Initialize chat interface
            chat = ChatInterface()
            logger.info("Initialized ChatInterface")

            # Generate questions using the chat interface
            logger.info(f"Generating {num_questions} questions for video {video_id}")
            raw_questions = chat.generate_questions(transcript_text, num_questions)
            logger.info(f"Received {len(raw_questions)} raw questions from LLM")

            if not raw_questions:
                logger.error("Failed to generate questions")
                self._log_error("generate_questions", "Failed to generate questions", video_id)
                return []

            # Process and format each question
            processed_questions = []
            for i, raw_question in enumerate(raw_questions, 1):
                try:
                    logger.info(f"Processing question {i}")
                    # Format the question
                    question = self._process_raw_question(raw_question, video_id, i)
                    if question:
                        logger.info(f"Successfully formatted question {i}")
                        # Save the question
                        if self.save_question(question, video_id, i):
                            logger.info(f"Successfully saved question {i}")
                            processed_questions.append(question)
                        else:
                            logger.error(f"Failed to save question {i}")
                    else:
                        logger.error(f"Failed to format question {i}")
                except Exception as e:
                    logger.error(f"Error processing question {i}: {str(e)}", exc_info=True)
                    self._log_error("process_question", str(e), video_id, section_num=i)

            logger.info(f"Generated {len(processed_questions)} questions for video {video_id}")
            return processed_questions
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}", exc_info=True)
            self._log_error("generate_questions", str(e), video_id)
            return []

    def _process_raw_question(self, raw_question: Dict, video_id: str, section_num: int) -> Optional[Dict]:
        """
        Process a raw question from the LLM into the required format.

        Args:
            raw_question (Dict): The raw question data from LLM
            video_id (str): The YouTube video ID
            section_num (int): The section number

        Returns:
            Optional[Dict]: Processed question or None if failed
        """
        try:
            # Extract fields from raw question
            question_data = {
                "video_id": video_id,
                "section_num": section_num,
                "introduction": raw_question.get("introduction", ""),
                "conversation": raw_question.get("conversation", ""),
                "question": raw_question.get("question", ""),
                "options": raw_question.get("options", []),
                "correct_answer": raw_question.get("correct_answer", 1)
            }

            # Validate question data
            if not question_data["question"] or not question_data["options"]:
                logger.error(f"Invalid question data for section {section_num}")
                return None

            return question_data
        except Exception as e:
            logger.error(f"Error processing raw question: {str(e)}")
            return None

    def _log_error(self, function_name: str, error_message: str, video_id: str = "", section_num: int = 0):
        """
        Log error to a JSON file.

        Args:
            function_name (str): The function where the error occurred
            error_message (str): The error message
            video_id (str): The YouTube video ID
            section_num (int): The section number
        """
        try:
            error_log_file = "backend/logs/errors.json"

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(error_log_file), exist_ok=True)

            # Load existing errors
            errors = []
            if os.path.exists(error_log_file):
                with open(error_log_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)

            # Add new error
            errors.append({
                "timestamp": datetime.now().isoformat(),
                "function": function_name,
                "error": error_message,
                "video_id": video_id,
                "section_num": section_num
            })

            # Save errors
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")

    def get_feedback(self, question: Dict, selected_answer: int) -> str:
        """
        Get feedback for a selected answer.

        Args:
            question (Dict): The question dictionary
            selected_answer (int): The selected answer index (1-based)

        Returns:
            str: Feedback message
        """
        try:
            correct_answer = question.get('correct_answer', 1)
            if selected_answer == correct_answer:
                return "正解です！(Correct!)"
            else:
                return f"不正解です。正解は {correct_answer} です。(Incorrect. The correct answer is {correct_answer}.)"
        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            return "エラーが発生しました。(An error occurred.)"
    
