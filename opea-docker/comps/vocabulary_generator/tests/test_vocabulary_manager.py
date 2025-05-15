import pytest
import asyncio
import os
import tempfile
import json
from datetime import datetime
from main import VocabularyManager

@pytest.fixture
async def vocab_manager():
    """Create a temporary vocabulary manager for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create a temporary config file
    config = {
        "api": {
            "ollama_endpoint": "http://localhost:9000/v1/chat/completions",
            "timeout": 30
        },
        "database": {
            "path": os.path.join(temp_dir, "test_vocabulary.db")
        },
        "storage": {
            "json_output_dir": os.path.join(temp_dir, "output"),
            "import_dir": os.path.join(temp_dir, "imports")
        },
        "jlpt_progression": {
            "N5": {
                "required_accuracy": 0.8,
                "minimum_reviews": 50,
                "next_level": "N4"
            }
        }
    }
    
    config_path = os.path.join(temp_dir, "test_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    # Initialize manager
    manager = VocabularyManager(config_path)
    await manager.initialize()
    
    yield manager
    
    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)
    os.rmdir(temp_dir)

@pytest.mark.asyncio
async def test_create_vocabulary_entry(vocab_manager):
    """Test creating a vocabulary entry"""
    entry = await vocab_manager.create_vocabulary_entry("食べる", "N5")
    assert 'kanji' in entry
    assert 'romaji' in entry
    assert 'english' in entry
    assert 'examples' in entry

@pytest.mark.asyncio
async def test_invalid_jlpt_level(vocab_manager):
    """Test invalid JLPT level handling"""
    with pytest.raises(ValueError):
        await vocab_manager.create_vocabulary_entry("食べる", "N6")

@pytest.mark.asyncio
async def test_study_session_creation(vocab_manager):
    """Test study session creation and management"""
    # Create a test user
    user_id = await vocab_manager.db.add_user({
        'name': 'Test User',
        'current_level': 'N5'
    })
    
    # Create a study session
    session = await vocab_manager.create_study_session('typing_tutor', 1, user_id)
    assert 'session_id' in session
    assert session['activity_type'] == 'typing_tutor'
    
    # End the session
    ended_session = await vocab_manager.end_study_session(session['session_id'])
    assert ended_session['end_time'] is not None
    assert ended_session['duration'] >= 0

@pytest.mark.asyncio
async def test_user_progression(vocab_manager):
    """Test user progression system"""
    # Create a test user
    user_id = await vocab_manager.db.add_user({
        'name': 'Test User',
        'current_level': 'N5'
    })
    
    # Get initial stats
    initial_stats = await vocab_manager.get_user_stats(user_id)
    assert initial_stats['current_level'] == 'N5'
    
    # Simulate enough correct reviews to progress
    session = await vocab_manager.create_study_session('typing_tutor', 1, user_id)
    for _ in range(60):  # More than minimum_reviews
        await vocab_manager.add_word_review(1, session['session_id'], True)
    
    # Check progression
    if await vocab_manager.check_progression('N5'):
        new_level = await vocab_manager.advance_level(user_id)
        assert new_level == 'N4'
        
        # Verify progression history
        history = await vocab_manager.get_progression_history(user_id)
        assert len(history) > 0
        assert history[0]['previous_level'] == 'N5'
        assert history[0]['new_level'] == 'N4' 