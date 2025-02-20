import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import aiosqlite
import asyncio

class DatabaseManager:
    def __init__(self, db_path: str = "data/vocabulary.db"):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with schema"""
        async with aiosqlite.connect(self.db_path) as db:
            with open('schema.sql', 'r') as schema_file:
                await db.executescript(schema_file.read())
            await db.commit()

    async def add_word_group(self, name: str) -> int:
        """Add a new word group and return its ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO word_groups (name) VALUES (?)",
                (name,)
            )
            await db.commit()
            return cursor.lastrowid

    async def add_word(self, word_data: Dict, group_id: int) -> int:
        """Add a new word to the database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO words (kanji, romaji, english, group_id)
                VALUES (?, ?, ?, ?)
                """,
                (word_data['kanji'], word_data['romaji'], 
                 word_data['english'], group_id)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_word(self, word_id: int) -> Optional[Dict]:
        """Retrieve a word by its ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id, kanji, romaji, english, group_id, 
                       correct_count, wrong_count
                FROM words WHERE id = ?
                """,
                (word_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'kanji': row[1],
                        'romaji': row[2],
                        'english': row[3],
                        'group_id': row[4],
                        'correct_count': row[5],
                        'wrong_count': row[6]
                    }
                return None

    async def get_words_by_group(self, group_id: int) -> List[Dict]:
        """Retrieve all words in a group"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id, kanji, romaji, english, 
                       correct_count, wrong_count
                FROM words WHERE group_id = ?
                """,
                (group_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'kanji': row[1],
                        'romaji': row[2],
                        'english': row[3],
                        'correct_count': row[4],
                        'wrong_count': row[5]
                    }
                    for row in rows
                ]

    async def add_study_session(self, session_data: Dict) -> int:
        """Add a new study session"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO study_sessions 
                (activity_type, group_id, duration, start_time, 
                 end_time, accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_data['activity_type'], session_data['group_id'],
                 session_data['duration'], session_data['start_time'],
                 session_data['end_time'], session_data['accuracy'])
            )
            await db.commit()
            return cursor.lastrowid

    async def add_word_review(self, review_data: Dict) -> int:
        """Add a word review item"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO word_review_items 
                (word_id, session_id, correct)
                VALUES (?, ?, ?)
                """,
                (review_data['word_id'], review_data['session_id'],
                 review_data['correct'])
            )
            await db.commit()
            return cursor.lastrowid

    async def get_word_stats(self, word_id: int) -> Dict:
        """Get statistics for a specific word"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT correct_count, wrong_count
                FROM words WHERE id = ?
                """,
                (word_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'correct_count': row[0],
                        'wrong_count': row[1],
                        'total_reviews': row[0] + row[1],
                        'accuracy': row[0] / (row[0] + row[1]) if (row[0] + row[1]) > 0 else 0
                    }
                return None
            
    async def add_user(self, user_data: Dict) -> int:
        """Add a new user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO users (name, current_level) VALUES (?, ?)",
                (user_data['name'], user_data['current_level'])
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
            "SELECT id, name, current_level FROM users WHERE id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'current_level': row[2]
                    }
                return None

    async def update_user_level(self, user_id: int, new_level: str):
        """Update user's JLPT level"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET current_level = ? WHERE id = ?",
                (new_level, user_id)
            )
            await db.commit()

    async def add_progression_history(self, history_data: Dict) -> int:
        """Record a level progression event"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO progression_history
                (user_id, previous_level, new_level)
                VALUES (?, ?, ?)
                """,
                (history_data['user_id'], history_data['previous_level'],
                 history_data['new_level'])
            )
            await db.commit()
            return cursor.lastrowid