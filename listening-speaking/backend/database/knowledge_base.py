# backend/database/knowledge_base.py

import sqlite3
import json
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests
import sys
import chromadb
from chromadb.config import Settings

# Add the backend directory to Python path using relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from backend.utils.helper import get_file_path
from backend.config import ServiceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/shared_db/logs/knowledge_base.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, db_path: str = "data/shared_db/knowledge_base.db"):
        """Initialize the database connection and ChromaDB client"""
        self.db_path = db_path

        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._create_tables()

        # Initialize ChromaDB client with v2 API
        try:
            self.chroma_client = chromadb.HttpClient(
                host="localhost",
                port=8000,
                settings=Settings(
                    chroma_api_impl="rest",
                    chroma_server_host="localhost",
                    chroma_server_http_port=8000,
                    allow_reset=True,
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )
            logger.info("Successfully initialized ChromaDB client")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise

        # Create or get collection
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name="transcripts",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Successfully initialized collection")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")
            raise

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

    def save_transcript(self, video_id: str, content: str, language: str = "ja") -> bool:
        """Save transcript to both SQLite and ChromaDB"""
        try:
            # First check if JSON file exists
            json_file = get_file_path("data/transcripts", video_id, "json")
            logger.info(f"Looking for transcript JSON file at: {json_file}")
            
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                        content = transcript_data.get('transcript', content)
                        language = transcript_data.get('language', language)
                    logger.info(f"Successfully read transcript from JSON file: {json_file}")
                except Exception as e:
                    logger.error(f"Error reading transcript JSON file: {str(e)}")

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
        """Save transcript to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO transcripts (video_id, content, language) VALUES (?, ?, ?)",
                    (video_id, content, language)
                )
                conn.commit()
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
        """Save question to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Ensure options is a JSON string
                options = question_data.get("options", [])
                if isinstance(options, list):
                    options_json = json.dumps(options, ensure_ascii=False)
                else:
                    options_json = options

                cursor.execute(
                    """
                    INSERT INTO questions
                    (video_id, section_num, introduction, conversation, question, options, correct_answer)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        question_data["video_id"],
                        question_data["section_num"],
                        question_data.get("introduction", ""),
                        question_data.get("conversation", ""),
                        question_data["question"],
                        options_json,
                        question_data.get("correct_answer", 1)
                    )
                )
                conn.commit()
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

    def get_question_by_id(self, question_id: int) -> Optional[Dict]:
        """Retrieve a question by its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "video_id": row[1],
                        "section_num": row[2],
                        "introduction": row[3],
                        "conversation": row[4],
                        "question": row[5],
                        "options": json.loads(row[6]) if row[6] else [],
                        "correct_answer": row[7],
                        "created_at": row[8],
                    }
                return None
        except Exception as e:
            logger.error(f"Error retrieving question by ID: {str(e)}")
            return None

    def update_question_image_path(self, question_id: int, image_path: str) -> bool:
        """Update the image path for a question."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE questions SET image_path = ? WHERE id = ?",
                    (image_path, question_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating question image path: {str(e)}")
            return False

    def get_questions(self, video_id: str) -> List[Dict]:
        """Retrieve questions for a video"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM questions WHERE video_id = ? ORDER BY section_num",
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
        """Generate embedding using the embeddings service"""
        try:
            # Use the dedicated embeddings service
            response = requests.post(
                "http://localhost:6000/embed",
                json={"texts": [text]}
            )
            response.raise_for_status()
            result = response.json()
            return result["embeddings"][0]
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def save_embedding(self, text: str, metadata: Dict[str, Any], collection_name: str) -> bool:
        """Save embedding to ChromaDB"""
        try:
            embedding = self.generate_embedding(text)
            if not embedding:
                return False

            # Get or create collection
            collection = self.chroma_client.get_collection(
                name=collection_name
            )
            
            # Add document to collection
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

            # Get collection
            collection = self.chroma_client.get_collection(
                name=collection_name
            )
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying similar items: {str(e)}")
            return []

    def find_similar_questions(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Find similar questions using ChromaDB"""
        return self.query_similar(query_text, "questions", top_k)

    def find_similar_transcripts(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Find similar transcripts using ChromaDB"""
        return self.query_similar(query_text, "transcripts", top_k)

    def log_image_generation_request(self, question_id: int, prompt: str) -> Optional[int]:
        """Log an image generation request"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO image_generation
                    (question_id, prompt, status)
                    VALUES (?, ?, 'pending')
                    """,
                    (question_id, prompt)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging image generation request: {str(e)}")
            return None

    def update_image_generation_status(self, request_id: int, status: str,
                                      error_message: Optional[str] = None) -> bool:
        """Update the status of an image generation request"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if status == 'completed':
                    cursor.execute(
                        """
                        UPDATE image_generation
                        SET status = ?, completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (status, request_id)
                    )
                elif status == 'failed':
                    cursor.execute(
                        """
                        UPDATE image_generation
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                        WHERE id = ?
                        """,
                        (status, error_message, request_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE image_generation
                        SET status = ?
                        WHERE id = ?
                        """,
                        (status, request_id)
                    )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating image generation status: {str(e)}")
            return False

    def get_pending_image_requests(self) -> List[Dict]:
        """Get all pending image generation requests"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT ig.id, ig.question_id, ig.prompt, q.video_id, q.section_num
                    FROM image_generation ig
                    JOIN questions q ON ig.question_id = q.id
                    WHERE ig.status = 'pending'
                    ORDER BY ig.created_at
                    """
                )
                requests = []
                for row in cursor.fetchall():
                    requests.append({
                        "id": row[0],
                        "question_id": row[1],
                        "prompt": row[2],
                        "video_id": row[3],
                        "section_num": row[4]
                    })
                return requests
        except Exception as e:
            logger.error(f"Error getting pending image requests: {str(e)}")
            return []

    def add_transcript(self, transcript_id: str, text: str, metadata: dict = None):
        try:
            self.collection.add(
                documents=[text],
                ids=[transcript_id],
                metadatas=[metadata] if metadata else None
            )
            logger.info(f"Successfully added transcript {transcript_id}")
        except Exception as e:
            logger.error(f"Failed to add transcript {transcript_id}: {str(e)}")
            raise

    def search_transcripts(self, query: str, n_results: int = 5):
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            logger.info(f"Successfully searched transcripts for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Failed to search transcripts: {str(e)}")
            raise