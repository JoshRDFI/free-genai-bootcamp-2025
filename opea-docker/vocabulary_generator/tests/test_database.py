import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from src.database import DatabaseManager

@pytest.fixture
async def db_manager():
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        db = DatabaseManager(db_path=tmp.name)
        await db.init_db("../../database/schema.sql")
        yield db
        # Cleanup will happen automatically when tmp is closed

@pytest.mark.asyncio
async def test_add_word_group(db_manager):
    group_id = await db_manager.add_word_group("Test Group")
    assert group_id > 0

@pytest.mark.asyncio
async def test_add_word(db_manager):
    # First create a group
    group_id = await db_manager.add_word_group("Test Group")
    
    # Add a word
    word_data = {
        'kanji': '食べる',
        'romaji': 'taberu',
        'english': 'to eat'
    }
    word_id = await db_manager.add_word(word_data, group_id)
    assert word_id > 0

@pytest.mark.asyncio
async def test_get_word(db_manager):
    # First create a group and add a word
    group_id = await db_manager.add_word_group("Test Group")
    word_data = {
        'kanji': '食べる',
        'romaji': 'taberu',
        'english': 'to eat'
    }
    word_id = await db_manager.add_word(word_data, group_id)
    
    # Retrieve the word
    word = await db_manager.get_word(word_id)
    assert word is not None
    assert word['kanji'] == '食べる'
    assert word['romaji'] == 'taberu'
    assert word['english'] == 'to eat'

@pytest.mark.asyncio
async def test_word_validation(db_manager):
    """Test word data validation"""
    group_id = await db_manager.add_word_group("Test Group")
    
    # Test missing required field
    with pytest.raises(ValueError):
        await db_manager.add_word({'kanji': 'テスト'}, group_id)
    
    # Test empty string
    with pytest.raises(ValueError):
        await db_manager.add_word({
            'kanji': '',
            'romaji': 'tesuto',
            'english': 'test'
        }, group_id)

@pytest.mark.asyncio
async def test_study_session(db_manager):
    # Create a group
    group_id = await db_manager.add_word_group("Test Group")
    
    # Create a study session
    session_data = {
        'activity_type': 'typing_tutor',
        'group_id': group_id,
        'start_time': '2024-03-20T10:00:00',
        'duration': 0,
        'end_time': None,
        'accuracy': 0.0
    }
    session_id = await db_manager.add_study_session(session_data)
    assert session_id > 0

@pytest.mark.asyncio
async def test_word_review(db_manager):
    # Create a group and add a word
    group_id = await db_manager.add_word_group("Test Group")
    word_data = {
        'kanji': '食べる',
        'romaji': 'taberu',
        'english': 'to eat'
    }
    word_id = await db_manager.add_word(word_data, group_id)
    
    # Create a study session
    session_data = {
        'activity_type': 'typing_tutor',
        'group_id': group_id,
        'start_time': '2024-03-20T10:00:00',
        'duration': 0,
        'end_time': None,
        'accuracy': 0.0
    }
    session_id = await db_manager.add_study_session(session_data)
    
    # Add a review
    review_data = {
        'word_id': word_id,
        'session_id': session_id,
        'correct': True
    }
    review_id = await db_manager.add_word_review(review_data)
    assert review_id > 0
    
    # Check word stats
    stats = await db_manager.get_word_stats(word_id)
    assert stats['correct_count'] == 1
    assert stats['wrong_count'] == 0

@pytest.mark.asyncio
async def test_database_backup(db_manager):
    """Test database backup functionality"""
    backup_path = await db_manager.backup_database()
    assert os.path.exists(backup_path)
    assert backup_path.endswith('.db')