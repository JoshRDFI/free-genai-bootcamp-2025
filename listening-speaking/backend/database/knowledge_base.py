# backend/database/knowledge_base.py

import sqlite3
import json
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from chromadb.config import Settings
from chromadb.client import Client
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, db_path: str = "backend/database/knowledge_base.db"):
        """Initialize the database connection and ChromaDB client"""
        self.db_path = db_path
        self._create_tables()

        # Initialize ChromaDB
        self.chroma_client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="backend/database/chroma"
        ))

        # Create or get collections
        self.transcript_collection = self.chroma_client.get_or_create_collection("transcripts")
        self.question_collection = self.chroma_client.get_or_create_collection("questions")

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
        """Save transcript to both SQLite and ChromaDB"""
        try:
            # Save to SQLite
            success = self._save_transcript_sqlite(video_id, content, language)
            if not success:
                return False

            # Save to ChromaDB
            metadata = {
                "video_id": video_id,
                "language": language,
                "type": "transcript",
                "created_at": datetime.now().isoformat()
            }
            return self.save_embedding(content, metadata, "transcripts")
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            return False

    def _save_transcript_sqlite(self, video_id: str, content: str, language: str) -> bool:
        """Save transcript to SQLite (original implementation)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transcripts (video_id, content, language) VALUES (?, ?, ?)",
                    (video_id, content, language)
                )
                return True
        except Exception as e:
            logger.error(f"Error saving transcript to SQLite: {str(e)}")
            return False

    def save_question(self, question_data: Dict[str, Any]) -> bool:
        """Save question to both SQLite and ChromaDB"""
        try:
            # Save to SQLite
            success = self._save_question_sqlite(question_data)
            if not success:
                return False

            # Prepare text for embedding
            question_text = f"{question_data.get('introduction', '')} {question_data.get('conversation', '')} {question_data['question']}"

            # Save to ChromaDB
            metadata = {
                "video_id": question_data["video_id"],
                "section_num": question_data["section_num"],
                "type": "question",
                "created_at": datetime.now().isoformat()
            }
            return self.save_embedding(question_text, metadata, "questions")
        except Exception as e:
            logger.error(f"Error saving question: {str(e)}")
            return False

    def _save_question_sqlite(self, question_data: Dict[str, Any]) -> bool:
        """Save question to SQLite (original implementation)"""
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
                        question_data.get("introduction"),
                        question_data.get("conversation"),
                        question_data["question"],
                        json.dumps(question_data.get("options", []), ensure_ascii=False),
                        question_data.get("correct_answer", 1)
                    )
                )
                return True
        except Exception as e:
            logger.error(f"Error saving question to SQLite: {str(e)}")
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
            logger.error(f"Error retrieving transcript: {str(e)}")
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
                        "introduction": row[3],
                        "conversation": row[4],
                        "question": row[5],
                        "options": json.loads(row[6]) if row[6] else [],
                        "correct_answer": row[7],
                        "created_at": row[8]
                    })
                return questions
        except Exception as e:
            logger.error(f"Error retrieving questions: {str(e)}")
            return []

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Ollama API"""
        try:
            response = requests.post(
                "http://localhost:11434/api/embed",
                json={"model": "llama-3.2", "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def save_embedding(self, text: str, metadata: Dict[str, Any], collection_name: str) -> bool:
        """Save embedding to ChromaDB"""
        try:
            embedding = self.generate_embedding(text)
            if not embedding:
                return False

            collection = self.chroma_client.get_collection(collection_name)
            collection.add(
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding],
                ids=[f"{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"]
            )
            return True
        except Exception as e:
            logger.error(f"Error saving embedding: {str(e)}")
            return False

    def query_similar(self, query_text: str, collection_name: str, top_k: int = 5) -> List[Dict]:
        """Query similar items from ChromaDB"""
        try:
            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                return []

            collection = self.chroma_client.get_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return results
        except Exception as e:
            logger.error(f"Error querying similar items: {str(e)}")
            return []

    def find_similar_questions(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Find similar questions using ChromaDB"""
        return self.query_similar(query_text, "questions", top_k)

    def find_similar_transcripts(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Find similar transcripts using ChromaDB"""
        return self.query_similar(query_text, "transcripts", top_k)