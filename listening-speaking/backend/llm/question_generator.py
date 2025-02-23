# backend/llm/question_generator.py

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from backend.utils.helper import (
    generate_timestamp,
    get_file_path,
    load_json_file,
    save_json_file
)

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

    def generate_questions(self, transcript: List[Dict], video_id: str) -> List[Dict]:
        """Generate questions from transcript"""
        # This is a placeholder - actual implementation would use LLM
        questions = []
        # Add implementation for question generation using LLM
        return questions