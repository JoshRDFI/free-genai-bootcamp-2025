# backend/database/knowledge_base.py

import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

class KnowledgeBase:
    def __init__(self, db_path: str = "backend/database/knowledge_base.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create transcripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    section_num INTEGER NOT NULL,
                    introduction TEXT,
                    conversation TEXT,
                    question TEXT NOT NULL,
                    options TEXT,
                    correct_answer INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def save_transcript(self, video_id: str, content: str, language: str = "ja") -> bool:
        """Save transcript to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transcripts (video_id, content, language) VALUES (?, ?, ?)",
                    (video_id, content, language)
                )
                return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

    def save_question(self, question_data: Dict[str, Any]) -> bool:
        """Save question to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO questions
                    (video_id, section_num, introduction, conversation, question, options, correct_answer)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        question_data["video_id"],
                        question_data["section_num"],
                        question_data.get("Introduction"),
                        question_data.get("Conversation"),
                        question_data["Question"],
                        json.dumps(question_data.get("Options", []), ensure_ascii=False),
                        question_data.get("correct_answer", 1)
                    )
                )
                return True
        except Exception as e:
            print(f"Error saving question: {str(e)}")
            return False

    def get_transcript(self, video_id: str) -> Optional[Dict]:
        """Retrieve transcript from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content, language, created_at FROM transcripts WHERE video_id = ?",
                    (video_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "content": result[0],
                        "language": result[1],
                        "created_at": result[2]
                    }
                return None
        except Exception as e:
            print(f"Error retrieving transcript: {str(e)}")
            return None

    def get_questions(self, video_id: str) -> List[Dict]:
        """Retrieve questions for a video"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM questions WHERE video_id = ? ORDER BY created_at",
                    (video_id,)
                )
                questions = []
                for row in cursor.fetchall():
                    questions.append({
                        "id": row[0],
                        "video_id": row[1],
                        "section_num": row[2],
                        "Introduction": row[3],
                        "Conversation": row[4],
                        "Question": row[5],
                        "Options": json.loads(row[6]) if row[6] else [],
                        "correct_answer": row[7],
                        "created_at": row[8]
                    })
                return questions
        except Exception as e:
            print(f"Error retrieving questions: {str(e)}")
            return []