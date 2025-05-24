import pytest
from src.database import DatabaseManager
import os
import tempfile

@pytest.fixture
async def db_manager():
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        db = DatabaseManager(db_path=tmp.name)
        await db.init_db("../../database/schema.sql")
        yield db

@pytest.mark.asyncio
async def test_user_progression(db_manager):
    # Create a test user
    user_id = await db_manager.add_user({
        'name': 'Test User',
        'current_level': 'N5'
    })
    
    # Create a word group
    group_id = await db_manager.add_word_group("Test Group")
    
    # Add some words
    words = [
        {'kanji': '食べる', 'romaji': 'taberu', 'english': 'to eat'},
        {'kanji': '飲む', 'romaji': 'nomu', 'english': 'to drink'},
        {'kanji': '行く', 'romaji': 'iku', 'english': 'to go'}
    ]
    
    word_ids = []
    for word in words:
        word_id = await db_manager.add_word(word, group_id)
        word_ids.append(word_id)
    
    # Create a study session
    session_data = {
        'activity_type': 'typing_tutor',
        'group_id': group_id,
        'start_time': '2024-03-20T10:00:00',
        'duration': 30,
        'end_time': '2024-03-20T10:30:00',
        'accuracy': 90.0
    }
    session_id = await db_manager.add_study_session(session_data)
    
    # Add reviews (all correct)
    for word_id in word_ids:
        review_data = {
            'word_id': word_id,
            'session_id': session_id,
            'correct': True
        }
        await db_manager.add_word_review(review_data)
    
    # Check user stats
    user = await db_manager.get_user(user_id)
    assert user['current_level'] == 'N5'
    
    # Add progression history
    history_data = {
        'user_id': user_id,
        'previous_level': 'N5',
        'new_level': 'N4'
    }
    history_id = await db_manager.add_progression_history(history_data)
    assert history_id > 0
    
    # Update user level
    await db_manager.update_user_level(user_id, 'N4')
    
    # Verify level update
    updated_user = await db_manager.get_user(user_id)
    assert updated_user['current_level'] == 'N4' 