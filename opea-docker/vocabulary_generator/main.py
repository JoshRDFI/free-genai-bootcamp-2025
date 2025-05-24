import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
import sqlite3

from src.generator import VocabularyGenerator
from src.validator import JLPTValidator
from src.converter import JapaneseConverter
from src.sentence_gen import SentenceGenerator
from src.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vocabulary_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VocabularyManager:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.generator = VocabularyGenerator(config_path)
        self.validator = JLPTValidator(config_path)
        self.converter = JapaneseConverter()
        self.sentence_gen = SentenceGenerator(self.config['api']['ollama_endpoint'])
        
        # Use absolute paths for database and storage
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, self.config['database']['path'])
        self.db = DatabaseManager(db_path)
        
        # Update storage paths to be absolute
        self.config['storage']['json_output_dir'] = os.path.join(base_dir, self.config['storage']['json_output_dir'])
        self.config['storage']['import_dir'] = os.path.join(base_dir, self.config['storage']['import_dir'])

    def _load_config(self, config_path: str) -> Dict:
        """Load and validate configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate required configuration sections
            required_sections = ['api', 'database', 'storage', 'jlpt_progression']
            missing_sections = [section for section in required_sections if section not in config]
            if missing_sections:
                raise ValueError(f"Missing required configuration sections: {missing_sections}")
            
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    async def initialize(self):
        """Initialize the database and create necessary directories"""
        try:
            # Use environment variables for paths
            db_path = os.getenv('DB_PATH', 'data/shared_db/db.sqlite3')
            schema_path = os.getenv('SCHEMA_PATH', '/app/database/schema.sql')
            
            # Debug information
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Looking for schema file at: {schema_path}")
            
            # Try to find schema file in multiple locations
            possible_schema_paths = [
                schema_path,
                '/app/data/shared_db/schema.sql',
                '/app/database/schema.sql'
            ]
            
            schema_found = False
            for path in possible_schema_paths:
                if os.path.exists(path):
                    schema_path = path
                    schema_found = True
                    logger.info(f"Found schema file at: {path}")
                    break
            
            if not schema_found:
                raise FileNotFoundError(f"Schema file not found in any of the expected locations: {possible_schema_paths}")
            
            # Update config with correct paths
            self.config['database']['path'] = db_path
            
            # Ensure data directory exists
            data_dir = os.path.dirname(db_path)
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize database with schema
            await self.db.init_db(schema_path)
            
            # Create other necessary directories
            Path(self.config['storage']['json_output_dir']).mkdir(parents=True, exist_ok=True)
            Path(self.config['storage']['import_dir']).mkdir(parents=True, exist_ok=True)
            
            # Create initial backup
            await self.db.backup_database()
            
            logger.info("Initialization completed successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    async def create_vocabulary_entry(self, word: str, level: str = "N5") -> Dict:
        """Create a new vocabulary entry with validation"""
        try:
            if not isinstance(word, str) or not word.strip():
                raise ValueError("Word must be a non-empty string")
            
            if level not in ['N5', 'N4', 'N3', 'N2', 'N1']:
                raise ValueError(f"Invalid JLPT level: {level}")
            
            entry = await self.generator.generate_vocabulary_entry(word, level)

            if not self.validator.validate_entry(entry, level):
                raise ValueError(f"Generated entry for '{word}' does not meet {level} requirements")

            examples = await self.sentence_gen.generate_examples(word, level)
            entry['examples'] = examples

            return entry
        except Exception as e:
            logger.error(f"Error creating vocabulary entry: {str(e)}")
            raise

    async def import_from_json(self, file_path: str, group_name: str) -> List[Dict]:
        """Import vocabulary from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        group_id = await self.db.add_word_group(group_name)
        imported_entries = []

        for entry in entries:
            if self.validator.validate_entry(entry, "N5"):
                word_id = await self.db.add_word(entry, group_id)
                entry['id'] = word_id
                imported_entries.append(entry)

        return imported_entries

    async def create_study_session(self, activity_type: str, group_id: int) -> Dict:
        """Create a new study session"""
        current_time = datetime.now().isoformat()
        session_data = {
            'activity_type': activity_type,
            'group_id': group_id,
            'start_time': current_time,
            'end_time': current_time,  # Set initial end_time same as start_time
            'duration': 0,
            'accuracy': 0.0
        }

        session_id = await self.db.add_study_session(session_data)
        return {'session_id': session_id, **session_data}

    async def end_study_session(self, session_id: int) -> Dict:
        """End a study session and calculate final metrics"""
        end_time = datetime.now()
        session = await self.db.get_study_session(session_id)

        if session:
            start_time = datetime.fromisoformat(session['start_time'])
            duration = int((end_time - start_time).total_seconds() / 60)  # Duration in minutes

            # Calculate session accuracy
            reviews = await self.db.get_session_reviews(session_id)
            correct_count = sum(1 for review in reviews if review['correct'])
            accuracy = correct_count / len(reviews) if reviews else 0.0

            # Update session
            await self.db.update_study_session(session_id, {
                'end_time': end_time.isoformat(),
                'duration': duration,
                'accuracy': accuracy * 100  # Store as percentage
            })

            return await self.db.get_study_session(session_id)
        return None

    async def add_word_review(self, word_id: int, session_id: int, correct: bool):
        """Add a word review result"""
        await self.db.add_word_review(word_id, session_id, correct)
        print(f"Added review for word {word_id} in session {session_id}: {'correct' if correct else 'incorrect'}")

    async def get_user_stats(self, user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        user = await self.db.get_user(user_id)
        sessions = await self.db.get_user_sessions(user_id)
        reviews = await self.db.get_user_reviews(user_id)

        total_reviews = len(reviews)
        correct_reviews = sum(1 for review in reviews if review['correct'])

        return {
            'current_level': user['current_level'],
            'total_sessions': len(sessions),
            'total_reviews': total_reviews,
            'accuracy': (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0,
            'study_time': sum(session['duration'] for session in sessions)
        }

    async def check_progression(self, current_level: str) -> bool:
        """Check if ready to progress to next JLPT level"""
        if current_level not in self.config['jlpt_progression']:
            return False

        criteria = self.config['jlpt_progression'][current_level]
        required_accuracy = criteria['required_accuracy']
        minimum_reviews = criteria['minimum_reviews']

        groups = await self.db.get_all_word_groups()
        total_reviews = 0
        total_correct = 0

        for group in groups:
            words = await self.db.get_words_by_group(group['id'])
            for word in words:
                total_correct += word['correct_count']
                total_reviews += word['correct_count'] + word['wrong_count']

        if total_reviews < minimum_reviews:
            return False

        accuracy = total_correct / total_reviews if total_reviews > 0 else 0
        return accuracy >= required_accuracy

    async def advance_level(self, user_id: int) -> Optional[str]:
        """Advance user to next JLPT level if eligible"""
        user = await self.db.get_user(user_id)
        current_level = user['current_level']

        if await self.check_progression(current_level):
            next_level = self.config['jlpt_progression'][current_level]['next_level']

            # Record progression history
            await self.db.add_progression_history({
                'user_id': user_id,
                'previous_level': current_level,
                'new_level': next_level
            })

            # Update user level
            await self.db.update_user_level(user_id, next_level)

            return next_level
        return None

    async def get_progression_history(self, user_id: int) -> List[Dict]:
        """Get user's JLPT level progression history"""
        return await self.db.get_progression_history(user_id)

async def main():
    """Example usage of the VocabularyManager"""
    manager = VocabularyManager()
    await manager.initialize()

    # Try to get existing group or create a new one
    group_name = "Test Group"
    try:
        # Try to create a new group
        group_id = await manager.db.add_word_group(group_name)
        print(f"Created new word group: {group_name}")
    except sqlite3.IntegrityError:
        # If group exists, get its ID
        async with manager.db.get_connection() as db:
            async with db.execute(
                "SELECT id FROM word_groups WHERE name = ?",
                (group_name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    group_id = row[0]
                    print(f"Using existing word group: {group_name}")
                else:
                    raise Exception("Failed to get existing word group")

    # Create some test vocabulary entries
    test_words = [
        {
            'kanji': '食べる',
            'romaji': 'taberu',
            'english': 'to eat'
        },
        {
            'kanji': '飲む',
            'romaji': 'nomu',
            'english': 'to drink'
        },
        {
            'kanji': '行く',
            'romaji': 'iku',
            'english': 'to go'
        }
    ]

    # Add words to the database and store their IDs
    added_words = []
    for word in test_words:
        word_id = await manager.db.add_word(word, group_id)
        word['id'] = word_id  # Store the ID in the word dictionary
        added_words.append(word)
        print(f"Added word: {word['kanji']} ({word['english']})")

    # Create study session
    session = await manager.create_study_session('typing_tutor', group_id)

    # Simulate some word reviews
    for word in added_words:
        await manager.add_word_review(word['id'], session['session_id'], True)

    # End session
    await manager.end_study_session(session['session_id'])

if __name__ == "__main__":
    asyncio.run(main())