# backend/database/knowledge_base.py

import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests

# Import ChromaDB classes
from chromadb.config import Settings
from chromadb.client import Client

class KnowledgeBase:
    def __init__(self, db_path: str = "backend/database/knowledge_base.db"):
        """Initialize the database connection and ChromaDB client"""
        self.db_path = db_path
        self._create_tables()

        # Initialize ChromaDB client with persistence directory
        self.chroma_client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="backend/database/chroma"
        ))
        # Get or create collections for transcripts and questions
        self.transcript_collection = self.chroma_client.get_or_create_collection("transcripts")
        self.question_collection = self.chroma_client.get_or_create_collection("questions")

    def _create_tables(self):
        """Create necessary SQLite tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Transcripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Questions table
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

    # --- Embedding Methods using Ollama and ChromaDB ---

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate an embedding using Ollama's endpoint"""
        try:
            response = requests.post(
                "http://localhost:11434/api/embed",
                json={"text": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None

    def save_embedding_to_chroma(self, text: str, metadata: Dict[str, Any], collection: str) -> bool:
        """Save embedding to the appropriate ChromaDB collection"""
        try:
            embedding = self.generate_embedding(text)
            if not embedding:
                print("Could not generate embedding.")
                return False

            # Choose the collection based on the argument
            col = self.chroma_client.get_collection(collection)
            # We use a timestamp-based id (could be adjusted as needed)
            doc_id = f"{collection}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            col.add(
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding],
                ids=[doc_id]
            )
            return True
        except Exception as e:
            print(f"Error saving embedding: {str(e)}")
            return False

    def query_similar(self, query_text: str, collection: str, top_k: int = 5) -> List[Dict]:
        """Query similar entries from a given ChromaDB collection"""
        try:
            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                return []
            col = self.chroma_client.get_collection(collection)
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return results
        except Exception as e:
            print(f"Error querying similar items: {str(e)}")
            return []

    # --- Existing SQLite Methods with ChromaDB augmentation ---

    def save_transcript(self, video_id: str, content: str, language: str = "ja") -> bool:
        """Save transcript to SQLite and ChromaDB"""
        try:
            # Save to SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transcripts (video_id, content, language) VALUES (?, ?, ?)",
                    (video_id, content, language)
                )
                conn.commit()

            # Save embedding to ChromaDB
            metadata = {
                "video_id": video_id,
                "language": language,
                "type": "transcript",
                "created_at": datetime.now().isoformat()
            }
            return self.save_embedding_to_chroma(content, metadata, "transcripts")
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

    def save_question(self, question_data: Dict[str, Any]) -> bool:
        """Save question to SQLite and ChromaDB"""
        try:
            # Save to SQLite
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
                conn.commit()

            # Prepare text for embedding (concatenate parts)
            combined_text = " ".join([
                question_data.get("Introduction", ""),
                question_data.get("Conversation", ""),
                question_data["Question"]
            ])
            metadata = {
                "video_id": question_data["video_id"],
                "section_num": question_data["section_num"],
                "type": "question",
                "created_at": datetime.now().isoformat()
            }
            return self.save_embedding_to_chroma(combined_text, metadata, "questions")
        except Exception as e:
            print(f"Error saving question: {str(e)}")
            return False

    def get_transcript(self, video_id: str) -> Optional[Dict]:
        """Retrieve transcript from SQLite"""
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
        """Retrieve questions for a video from SQLite"""
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

    # --- Methods for testing similarity (RAG queries) ---

    def find_similar_transcripts(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Return similar transcripts using ChromaDB"""
        return self.query_similar(query_text, "transcripts", top_k)

    def find_similar_questions(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Return similar questions using ChromaDB"""
        return self.query_similar(query_text, "questions", top_k)