import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.generator import VocabularyGenerator
from src.validator import JLPTValidator
from src.converter import JapaneseConverter
from src.sentence_gen import SentenceGenerator
from src.database import DatabaseManager

class VocabularyManager:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.generator = VocabularyGenerator(config_path)
        self.validator = JLPTValidator(config_path)
        self.converter = JapaneseConverter()
        self.sentence_gen = SentenceGenerator(self.config['api']['ollama_endpoint'])
        self.db = DatabaseManager(self.config['database']['path'])

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def initialize(self):
        """Initialize the database and create necessary directories"""
        await self.db.init_db()
        Path(self.config['storage']['json_output_dir']).mkdir(parents=True, exist_ok=True)
        Path(self.config['storage']['import_dir']).mkdir(parents=True, exist_ok=True)

    async def create_vocabulary_entry(self, word: str, level: str = "N5") -> Dict:
        """Create a new vocabulary entry with validation"""
        entry = await self.generator.generate_vocabulary_entry(word, level)

        if not self.validator.validate_entry(entry, level):
            raise ValueError(f"Generated entry for '{word}' does not meet {level} requirements")

        examples = await self.sentence_gen.generate_examples(word, level)
        entry['examples'] = examples

        return entry

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

    async def create_study_session(self, activity_type: str, group_id: int, user_id: int) -> Dict:
        """Create a new study session with user tracking"""
        session_data = {
            'activity_type': activity_type,
            'group_id': group_id,
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
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
        """Add a word review result and update progression"""
        review_data = {
            'word_id': word_id,
            'session_id': session_id,
            'correct': correct
        }
        await self.db.add_word_review(review_data)

        # Check progression after review
        session = await self.db.get_study_session(session_id)
        if session:
            user_stats = await self.get_user_stats(session['user_id'])
            if await self.check_progression(user_stats['current_level']):
                await self.advance_level(session['user_id'])

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
    """Example usage of the VocabularyManager with progression system"""
    manager = VocabularyManager()
    await manager.initialize()

    # Create a test user
    user_id = await manager.db.add_user({
        'name': 'Test User',
        'current_level': 'N5'
    })

    # Import vocabulary
    imported = await manager.import_from_json(
        'data/data_verbs.json',
        'Core Verbs'
    )
    print(f"Imported {len(imported)} verbs")

    # Create study session
    session = await manager.create_study_session('typing_tutor', 1, user_id)

    # Simulate some word reviews
    for word_id in range(1, 6):
        await manager.add_word_review(word_id, session['session_id'], True)

    # End session
    await manager.end_study_session(session['session_id'])

    # Check progression
    user_stats = await manager.get_user_stats(user_id)
    if await manager.check_progression(user_stats['current_level']):
        new_level = await manager.advance_level(user_id)
        if new_level:
            print(f"Congratulations! Advanced to {new_level}")

    # Display progression history
    history = await manager.get_progression_history(user_id)
    for entry in history:
        print(f"Progressed from {entry['previous_level']} to {entry['new_level']} on {entry['progressed_at']}")

if __name__ == "__main__":
    asyncio.run(main())