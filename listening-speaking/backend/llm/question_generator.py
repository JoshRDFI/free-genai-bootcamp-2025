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
from backend.image.image_generator import ImageGenerator
from backend.image.prompt_generator import ImagePromptGenerator

# Get the absolute path to the logs directory
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
# Create logs directory if it doesn't exist
os.makedirs(logs_dir, exist_ok=True)
# Create the log file path
log_file = os.path.join(logs_dir, "question_generator.log")

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:  # Only add handlers if they don't exist
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class QuestionGenerator:
    def __init__(self):
        """Initialize the question generator"""
        self.questions_file = get_file_path("data", "stored_questions", "json")
        self.image_generator = ImageGenerator()
        self.prompt_generator = ImagePromptGenerator(self.image_generator.llm_client)

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

            # Convert the new question structure to the expected format
            formatted_question = {
                "Question": question.get("question", ""),
                "Options": question.get("options", []),
                "images": question.get("images", {})
            }

            # Add new question with the expected structure
            questions[timestamp] = {
                "question": formatted_question,
                "video_id": video_id,
                "section_num": section_num,
                "category": question.get("category", "General"),
                "practice_type": "Dialogue Practice",  # Default practice type
                "topic": question.get("category", "General"),  # Use category as topic
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save to JSON file
            if not save_json_file(self.questions_file, questions):
                logger.error(f"Failed to save questions to {self.questions_file}")
                return False

            logger.info(f"Successfully saved question {timestamp} to {self.questions_file}")

            # Save to text file
            text_file = get_file_path(
                "data/questions",
                f"{video_id}_section{section_num}",
                "txt"
            )

            with open(text_file, 'w', encoding='utf-8') as f:
                f.write("<question>\n")
                f.write(f"Category: {question.get('category', 'General')}\n\n")
                f.write(f"Question: {question.get('question', '')}\n\n")
                f.write("Options:\n")
                for i, option in enumerate(question.get('options', []), 1):
                    f.write(f"{i}. {option}\n")
                f.write(f"\nCorrect Answer: {question.get('correct_answer', 1)}\n")
                f.write("</question>\n")

            return True
        except Exception as e:
            logger.error(f"Error saving question: {str(e)}")
            return False

    def generate_questions(self, transcript: List[Dict], video_id: str, num_questions: int = 3) -> List[Dict]:
        """Generate questions from transcript using LLM."""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("backend/logs", exist_ok=True)

            # Extract text from transcript
            try:
                transcript_text = "\n".join(item["text"] for item in transcript)
                logger.info(f"Extracted transcript text for video {video_id}")
            except Exception as e:
                logger.error(f"Failed to extract transcript text: {str(e)}")
                raise ValueError(f"Invalid transcript format: {str(e)}")

            # Initialize chat interface
            try:
                chat = ChatInterface()
                logger.info("Initialized ChatInterface")
            except Exception as e:
                logger.error(f"Failed to initialize ChatInterface: {str(e)}")
                raise RuntimeError(f"Failed to initialize LLM service: {str(e)}")

            # Generate questions using the chat interface
            try:
                logger.info(f"Generating {num_questions} questions for video {video_id}")
                raw_questions = chat.generate_questions(transcript_text, num_questions)
                logger.info(f"Received {len(raw_questions)} questions from LLM")
            except (TimeoutError, ConnectionError) as e:
                logger.error(f"LLM service connection error: {str(e)}")
                raise
            except ValueError as e:
                logger.error(f"LLM response validation error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in LLM question generation: {str(e)}")
                raise RuntimeError(f"Failed to generate questions: {str(e)}")

            # Process and format each question
            processed_questions = []
            for i, raw_question in enumerate(raw_questions, 1):
                try:
                    logger.info(f"Processing question {i}")
                    
                    # Generate image prompts for each option
                    prompts = self.prompt_generator.generate_prompts(
                        raw_question.get("Question", ""),
                        raw_question.get("Options", [])
                    )
                    
                    # Generate images for each option
                    base_filename = f"question_{video_id}_{i}"
                    image_paths = self.image_generator.generate_option_images(prompts, base_filename)
                    
                    # Create the question object with images
                    question_obj = {
                        "video_id": video_id,
                        "section_num": i,
                        "category": raw_question.get("Category", "General"),
                        "question": raw_question.get("Question", ""),
                        "options": raw_question.get("Options", []),
                        "correct_answer": raw_question.get("CorrectAnswer", 1),
                        "images": image_paths
                    }
                    
                    # Save the question
                    if self.save_question(question_obj, video_id, i):
                        logger.info(f"Successfully saved question {i}")
                        processed_questions.append(question_obj)
                    else:
                        logger.error(f"Failed to save question {i}")
                        
                except Exception as e:
                    logger.error(f"Error processing question {i}: {str(e)}", exc_info=True)
                    continue

            if not processed_questions:
                logger.error("No questions were successfully processed")
                raise RuntimeError("Failed to process any questions")

            logger.info(f"Successfully generated {len(processed_questions)} questions for video {video_id}")
            return processed_questions

        except Exception as e:
            logger.error(f"Unexpected error in generate_questions: {str(e)}", exc_info=True)
            raise

    def _process_raw_question(self, raw_question: Dict, video_id: str, section_num: int) -> Optional[Dict]:
        """Process a raw question from the LLM into the required format."""
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

    def generate_image_for_old_questions(self):
        """Generate images for old questions that do not have an image_path."""
        logger.info("Starting image generation for old questions")
        try:
            # Load existing questions from JSON file
            questions = load_json_file(self.questions_file) or {}
            logger.info(f"Loaded {len(questions)} questions from JSON file.")
            if not questions:
                logger.info("No stored questions found.")
                return

            # Get absolute path for images directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            images_dir = os.path.join(project_root, "backend", "data", "images")
            
            logger.info(f"Using absolute images directory path: {images_dir}")
            
            # Ensure images directory exists
            os.makedirs(images_dir, exist_ok=True)
            
            # Check directory permissions and contents
            if not os.access(images_dir, os.W_OK):
                logger.error(f"No write permission for directory: {images_dir}")
                return
                
            # List current contents of images directory
            existing_files = os.listdir(images_dir)
            logger.info(f"Current contents of images directory: {existing_files}")
            
            image_generator = ImageGenerator()
            updated = False
            failed_questions = []

            for qid, qdata in questions.items():
                try:
                    question = qdata.get("question", {})
                    base_filename = f"question_{qid}"
                    
                    logger.info(f"Processing question {qid}")
                    
                    # Generate prompts for each option
                    prompts = self.prompt_generator.generate_prompts(
                        question.get("Question", ""),
                        question.get("Options", [])
                    )
                    
                    # Generate images for each option
                    image_paths = image_generator.generate_option_images(prompts, base_filename)
                    
                    if image_paths:
                        # Update question with new images structure
                        question["images"] = image_paths
                        # Remove old image_path if it exists
                        question.pop("image_path", None)
                        updated = True
                        logger.info(f"Successfully generated images for question {qid}")
                    else:
                        logger.error(f"Failed to generate images for question {qid}")
                        failed_questions.append(qid)
                        
                except Exception as e:
                    logger.error(f"Error processing question {qid}: {str(e)}", exc_info=True)
                    failed_questions.append(qid)
                    continue

            if updated:
                if save_json_file(self.questions_file, questions):
                    logger.info("Successfully updated questions file with new image paths")
                else:
                    logger.error("Failed to save updated questions file")

            if failed_questions:
                logger.warning(f"Failed to generate images for {len(failed_questions)} questions: {failed_questions}")
            else:
                logger.info("Successfully processed all questions")

        except Exception as e:
            logger.error(f"Error in generate_image_for_old_questions: {str(e)}", exc_info=True)
            raise
    
