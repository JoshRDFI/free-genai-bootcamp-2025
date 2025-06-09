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
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "../data/shared_db/db.sqlite3", pool_size: int = 5):
        print(f"DEBUG: DatabaseManager - __init__ started. DB Path: {db_path}") # DEBUG
        """Initialize database manager with shared database path"""
        # Use environment variable if available, otherwise use provided path
        self.db_path = os.getenv('DB_PATH', db_path)
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)
        self._pool_initialized = False
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

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
        required_fields = {'kanji', 'romaji', 'english', 'parts', 'group_id'}
        if not all(field in word_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields - set(word_data.keys())}")
        
        if not isinstance(word_data['kanji'], str) or not word_data['kanji'].strip():
            raise ValueError("Kanji must be a non-empty string")
        
        if not isinstance(word_data['romaji'], str) or not word_data['romaji'].strip():
            raise ValueError("Romaji must be a non-empty string")
        
        if not isinstance(word_data['english'], str) or not word_data['english'].strip():
            raise ValueError("English must be a non-empty string")
        
        if not isinstance(word_data['parts'], str):
            raise ValueError("Parts must be a string (JSON format expected)")
        
        try:
            json.loads(word_data['parts'])
        except json.JSONDecodeError:
            raise ValueError("Parts must be a valid JSON string")
        
        if not isinstance(word_data['group_id'], int):
            raise ValueError("group_id must be an integer for the legacy words.group_id column")
        
        return True

    def _validate_session_data(self, session_data: Dict) -> bool:
        """Validate session data before insertion"""
        required_fields = {'activity_type', 'group_id', 'start_time', 'user_id'}
        if not all(field in session_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields - set(session_data.keys())}")
        
        if not isinstance(session_data['user_id'], int):
            raise ValueError("user_id must be an integer")

        valid_activities = {'typing_tutor', 'adventure_mud', 'flashcards'}
        if session_data['activity_type'] not in valid_activities:
            raise ValueError(f"Invalid activity type. Must be one of: {valid_activities}")
        
        return True

    async def backup_database(self, backup_dir: str = "data/backups") -> str:
        """Create a backup of the database if it exists"""
        try:
            # Skip backup if database doesn't exist
            if not os.path.exists(self.db_path):
                logger.info("Database doesn't exist yet, skipping backup")
                return None
                
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

    async def init_db(self):
        """Initialize the connection pool"""
        await self._initialize_pool()

    async def add_word(self, word_data: Dict) -> int:
        """Add a new word to the database. word_data must include 'group_id' for the legacy words.group_id NOT NULL constraint.
           Actual group associations are managed via add_word_to_group."""
        # group_id from word_data is for the words.group_id column (legacy, but NOT NULL)
        # The parts field is also new.
        self._validate_word_data(word_data)
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO words (kanji, romaji, english, parts, group_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (word_data['kanji'], word_data['romaji'], 
                 word_data['english'], word_data['parts'], word_data['group_id'])
            )
            await db.commit()
            return cursor.lastrowid

    async def add_word_to_group(self, word_id: int, group_id: int) -> None:
        """Associate a word with a group in the join table."""
        async with self.get_connection() as db:
            try:
                await db.execute(
                    "INSERT INTO word_to_group_join (word_id, group_id) VALUES (?, ?)",
                    (word_id, group_id)
                )
                await db.commit()
                logger.info(f"Word ID {word_id} associated with Group ID {group_id}")
            except sqlite3.IntegrityError:
                logger.warning(f"Word ID {word_id} is already associated with Group ID {group_id} or invalid ID.")
                # Optionally re-raise or handle as needed

    async def remove_word_from_group(self, word_id: int, group_id: int) -> None:
        """Remove the association of a word from a group."""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "DELETE FROM word_to_group_join WHERE word_id = ? AND group_id = ?",
                (word_id, group_id)
            )
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Word ID {word_id} disassociated from Group ID {group_id}")
            else:
                logger.warning(f"No association found for Word ID {word_id} and Group ID {group_id} to remove.")

    async def add_word_group(self, name: str) -> int:
        """
        Add a new word group and return its ID, or return existing group's ID if it exists.

        Args:
            name (str): The name of the word group to add

        Returns:
            int: The ID of the word group (either existing or newly created)

        Raises:
            ValueError: If name is empty or invalid
            sqlite3.Error: If there's a database error
        """
        if not name or not isinstance(name, str):
            raise ValueError("Word group name must be a non-empty string")

        name = name.strip()  # Remove leading/trailing whitespace

        try:
            async with self.get_connection() as db:
                # First check if the group exists
                async with db.execute(
                    "SELECT id FROM word_groups WHERE name = ?",
                    (name,)
                ) as cursor:
                    existing_group = await cursor.fetchone()
                    if existing_group:
                        logger.info(f"Word group '{name}' already exists with ID {existing_group[0]}")
                        return existing_group[0]

                # If we get here, the group doesn't exist, so create it
                cursor = await db.execute(
                    "INSERT INTO word_groups (name) VALUES (?)",
                    (name,)
                )
                await db.commit()
                new_id = cursor.lastrowid
                logger.info(f"Created new word group '{name}' with ID {new_id}")
                return new_id

        except sqlite3.Error as e:
            logger.error(f"Database error while adding word group '{name}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while adding word group '{name}': {str(e)}")
            raise

    async def get_word(self, word_id: int) -> Optional[Dict]:
        """Retrieve a word by its ID"""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, kanji, romaji, english, group_id, parts,
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
                        'legacy_group_id': row[4], # Renamed for clarity
                        'parts': row[5],
                        'correct_count': row[6],
                        'wrong_count': row[7]
                    }
                return None

    async def get_words_by_group(self, group_id: int) -> List[Dict]:
        """Retrieve all words associated with a group via the join table"""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT w.id, w.kanji, w.romaji, w.english, w.parts,
                       w.correct_count, w.wrong_count
                FROM words w
                JOIN word_to_group_join wtg ON w.id = wtg.word_id
                WHERE wtg.group_id = ?
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
                        'parts': row[4],
                        'correct_count': row[5],
                        'wrong_count': row[6]
                    }
                    for row in rows
                ]

    async def get_groups_for_word(self, word_id: int) -> List[Dict]:
        """Retrieve all groups a word is associated with."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT wg.id, wg.name, wg.level, wg.words_count
                FROM word_groups wg
                JOIN word_to_group_join wtg ON wg.id = wtg.group_id
                WHERE wtg.word_id = ?
                ORDER BY wg.name ASC
                """,
                (word_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'level': row[2],
                        'words_count': row[3]
                    }
                    for row in rows
                ]

    async def get_study_session(self, session_id: int) -> Optional[Dict]:
        """Retrieve a study session by its ID"""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, activity_type, group_id, user_id, duration, 
                       start_time, end_time, accuracy
                FROM study_sessions WHERE id = ?
                """,
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'activity_type': row[1],
                        'group_id': row[2],
                        'user_id': row[3],
                        'duration': row[4],
                        'start_time': row[5],
                        'end_time': row[6],
                        'accuracy': row[7]
                    }
                return None

    async def add_study_session(self, session_data: Dict) -> int:
        """Add a new study session"""
        self._validate_session_data(session_data)
        
        async with self.get_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO study_sessions 
                (activity_type, group_id, user_id, duration, start_time, 
                 end_time, accuracy)
                VALUES (?, ?, ?, ?, ?, ?, ?) 
                """,
                (session_data['activity_type'], session_data['group_id'],
                 session_data['user_id'],
                 session_data.get('duration', 0), session_data['start_time'],
                 session_data['end_time'], session_data.get('accuracy', 0.0))
            )
            await db.commit()
            return cursor.lastrowid

    async def update_study_session(self, session_id: int, data: Dict) -> None:
        """Update an existing study session."""
        async with self.get_connection() as db:
            await db.execute(
                """UPDATE study_sessions
                   SET end_time = ?, duration = ?, accuracy = ?
                   WHERE id = ?""",
                (data.get('end_time'), data.get('duration'), 
                 data.get('accuracy'), session_id)
            )
            await db.commit()

    async def add_word_review(self, review_data: Dict) -> int:
        """Add a word review item"""
        async with self.get_connection() as db:
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

    async def get_session_reviews(self, session_id: int) -> List[Dict]:
        """Retrieve all reviews for a given session_id."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, word_id, session_id, correct
                FROM word_review_items 
                WHERE session_id = ?
                """,
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'word_id': row[1],
                        'session_id': row[2],
                        'correct': row[3]
                    }
                    for row in rows
                ]

    async def get_word_stats(self, word_id: int) -> Dict:
        """Get statistics for a specific word"""
        async with self.get_connection() as db:
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

    async def get_progression_history(self, user_id: int) -> List[Dict]:
        """Get JLPT level progression history for a specific user."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, user_id, previous_level, new_level, progressed_at
                FROM progression_history
                WHERE user_id = ? 
                ORDER BY progressed_at DESC
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'id': row[0],
                    'user_id': row[1],
                    'previous_level': row[2],
                    'new_level': row[3],
                    'progressed_at': row[4]
                } for row in rows]

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Retrieves a user by their ID."""
        async with self.get_connection() as db:
            async with db.execute(
                """SELECT id, name, current_level, created_at FROM users WHERE id = ?""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'current_level': row[2],
                        'created_at': row[3]
                    }
                else:
                    logger.warning(f"User with id {user_id} not found.")
                    return None

    async def add_user(self, user_data: Dict) -> int:
        """Adds a new user to the database. Expects 'id', 'name', 'current_level' in user_data."""
        user_id = user_data.get('id')
        name = user_data.get('name')
        current_level = user_data.get('current_level', 'N5')

        if user_id is None or name is None:
            raise ValueError("User ID and Name are required to add a user.")
        
        async with self.get_connection() as db:
            try:
                cursor = await db.execute(
                    "INSERT INTO users (id, name, current_level) VALUES (?, ?, ?)",
                    (user_id, name, current_level)
                )
                await db.commit()
                logger.info(f"User '{name}' with ID {user_id} added.")
                return cursor.lastrowid # or user_id, since we are specifying it
            except sqlite3.IntegrityError as e:
                # This can happen if a user with the same ID or name (UNIQUE constraint) already exists
                logger.warning(f"Could not add user ID {user_id}, Name '{name}'. It might already exist: {e}")
                # Check if it exists to return the ID if the issue was an attempt to re-add
                existing_user = await self.get_user(user_id)
                if existing_user and existing_user['name'] == name:
                    return user_id # Return existing user's ID
                raise # Re-raise if it's another integrity error
    
    async def ensure_default_user_exists(self, user_id: int, name: str, level: str) -> int:
        """Ensures the default user exists, creates if not. Returns the user ID."""
        user = await self.get_user(user_id)
        if user is None:
            logger.info(f"Default user (ID: {user_id}) not found. Creating...")
            await self.add_user({'id': user_id, 'name': name, 'current_level': level})
            return user_id
        else:
            logger.info(f"Default user (ID: {user_id}, Name: {user['name']}) already exists.")
            return user['id']

    async def add_progression_history(self, data: Dict) -> int:
        """
        Adds a new entry to the progression history.
        Expects 'user_id', 'previous_level', and 'new_level' in data.
        """
        user_id = data.get('user_id')
        previous_level = data.get('previous_level')
        new_level = data.get('new_level')

        if user_id is None or not isinstance(user_id, int):
            logger.error("add_progression_history called without a valid user_id in data")
            raise ValueError("user_id (int) is required in data for add_progression_history")
        if not previous_level or not new_level:
            logger.error("add_progression_history called without previous_level or new_level in data")
            raise ValueError("previous_level and new_level are required in data for add_progression_history")

        async with self.get_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO progression_history (user_id, previous_level, new_level)
                VALUES (?, ?, ?)
                """,
                (user_id, previous_level, new_level)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_user_level(self, user_id: int, new_level: str) -> None:
        """Updates the user's current_level in the users table."""
        if not isinstance(user_id, int):
            logger.error("update_user_level called with invalid user_id type")
            raise ValueError("user_id must be an integer")
        if new_level not in ('N5', 'N4', 'N3', 'N2', 'N1'):
            logger.error(f"update_user_level called with invalid new_level: {new_level}")
            raise ValueError("Invalid JLPT level for new_level")

        async with self.get_connection() as db:
            cursor = await db.execute(
                """UPDATE users SET current_level = ? WHERE id = ?""",
                (new_level, user_id)
            )
            await db.commit()
            if cursor.rowcount == 0:
                logger.warning(f"update_user_level: User with id {user_id} not found, no update performed.")
            else:
                logger.info(f"User {user_id} current_level updated to {new_level}.")

    async def get_all_word_groups(self) -> List[Dict]:
        """Retrieve all word groups."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, name, level, words_count FROM word_groups
                ORDER BY name ASC
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'level': row[2],
                        'words_count': row[3]
                    }
                    for row in rows
                ]

    async def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Retrieves all study sessions for a specific user."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT id, activity_type, group_id, user_id, duration, 
                       start_time, end_time, accuracy
                FROM study_sessions
                WHERE user_id = ? 
                ORDER BY start_time DESC
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'activity_type': row[1],
                        'group_id': row[2],
                        'user_id': row[3],
                        'duration': row[4],
                        'start_time': row[5],
                        'end_time': row[6],
                        'accuracy': row[7]
                    }
                    for row in rows
                ]

    async def get_user_reviews(self, user_id: int) -> List[Dict]:
        """Retrieves all word reviews for a specific user by joining through study_sessions."""
        async with self.get_connection() as db:
            async with db.execute(
                """
                SELECT r.id, r.word_id, r.session_id, r.correct, r.reviewed_at, s.user_id
                FROM word_review_items r
                JOIN study_sessions s ON r.session_id = s.id
                WHERE s.user_id = ?
                ORDER BY r.reviewed_at DESC
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'word_id': row[1],
                        'session_id': row[2],
                        'correct': row[3],
                        'reviewed_at': row[4],
                        'user_id': row[5]
                    }
                    for row in rows
                ]