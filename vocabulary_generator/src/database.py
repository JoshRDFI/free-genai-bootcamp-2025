import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import aiosqlite
import asyncio
import os
import shutil
from pathlib import Path
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/vocabulary.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)
        self._pool_initialized = False

    async def _initialize_pool(self):
        """Initialize the connection pool"""
        if not self._pool_initialized:
            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(self.db_path)
                await self.pool.put(conn)
            self._pool_initialized = True
            logger.info(f"Database connection pool initialized with {self.pool_size} connections")

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self._pool_initialized:
            await self._initialize_pool()
        
        conn = await self.pool.get()
        try:
            yield conn
        finally:
            await self.pool.put(conn)

    def _validate_word_data(self, word_data: Dict) -> bool:
        """Validate word data before insertion"""
        required_fields = {'kanji', 'romaji', 'english'}
        if not all(field in word_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields - set(word_data.keys())}")
        
        if not isinstance(word_data['kanji'], str) or not word_data['kanji'].strip():
            raise ValueError("Kanji must be a non-empty string")
        
        if not isinstance(word_data['romaji'], str) or not word_data['romaji'].strip():
            raise ValueError("Romaji must be a non-empty string")
        
        if not isinstance(word_data['english'], str) or not word_data['english'].strip():
            raise ValueError("English must be a non-empty string")
        
        return True

    def _validate_session_data(self, session_data: Dict) -> bool:
        """Validate session data before insertion"""
        required_fields = {'activity_type', 'group_id', 'start_time'}
        if not all(field in session_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields - set(session_data.keys())}")
        
        valid_activities = {'typing_tutor', 'adventure_mud', 'flashcards'}
        if session_data['activity_type'] not in valid_activities:
            raise ValueError(f"Invalid activity type. Must be one of: {valid_activities}")
        
        return True

    async def backup_database(self, backup_dir: str = "data/backups") -> str:
        """Create a backup of the database"""
        try:
            # Create backup directory if it doesn't exist
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"vocabulary_{timestamp}.db")
            
            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            
            # Clean up old backups (keep last 5)
            backups = sorted(Path(backup_dir).glob("vocabulary_*.db"))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
            
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            raise

    async def init_db(self, schema_path: str):
        """Initialize database with schema"""
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Check if database already exists
        db_exists = os.path.exists(self.db_path)
        
        if not db_exists:
            async with aiosqlite.connect(self.db_path) as db:
                # Read and execute schema
                with open(schema_path, 'r') as schema_file:
                    await db.executescript(schema_file.read())
                await db.commit()
                logger.info(f"Database initialized at {self.db_path}")
        else:
            logger.info(f"Database already exists at {self.db_path}")
            
        # Initialize connection pool
        await self._initialize_pool()

    async def add_word(self, word_data: Dict, group_id: int) -> int:
        """Add a new word to the database"""
        self._validate_word_data(word_data)
        
        async with self.get_connection() as db:
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

    async def add_word_group(self, name: str) -> int:
        """Add a new word group and return its ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO word_groups (name) VALUES (?)",
                (name,)
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
        self._validate_session_data(session_data)
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO study_sessions 
                (activity_type, group_id, duration, start_time, 
                 end_time, accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_data['activity_type'], session_data['group_id'],
                 session_data.get('duration', 0), session_data['start_time'],
                 session_data.get('end_time'), session_data.get('accuracy', 0.0))
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