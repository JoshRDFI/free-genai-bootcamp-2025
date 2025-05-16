# database/knowledge_base.py
import json
from .connection import SQLiteConnection, ChromaDBConnection

class KnowledgeBase:
    def __init__(self):
        self.sqlite_conn = SQLiteConnection.get_instance().get_connection()
        self.chroma_client = ChromaDBConnection.get_instance()
        self.collection = self.chroma_client.get_or_create_collection("transcripts")

    def save_transcript(self, video_id, transcript_text):
        # Save to SQLite
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO transcripts (video_id, transcript) VALUES (?, ?)",
            (video_id, transcript_text)
        )
        self.sqlite_conn.commit()

        # Save to ChromaDB
        self.collection.add(
            documents=[transcript_text],
            metadatas=[{"video_id": video_id}],
            ids=[video_id]
        )

    def find_similar_transcripts(self, query, limit=5):
        # Query ChromaDB for similar transcripts
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        return results

    def get_transcript(self, video_id):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM transcripts WHERE video_id = ?", (video_id,))
        return cursor.fetchone()

    def save_question(self, transcript_id, question_data):
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "INSERT INTO questions (transcript_id, question, options, correct_option) VALUES (?, ?, ?, ?)",
            (
                transcript_id,
                question_data["Question"],
                json.dumps(question_data["Options"]),
                question_data["CorrectOption"]
            )
        )
        self.sqlite_conn.commit()
        return cursor.lastrowid

    def get_all_questions(self):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM questions")
        return cursor.fetchall()