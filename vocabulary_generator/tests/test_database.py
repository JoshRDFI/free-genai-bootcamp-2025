import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from src.database import DatabaseManager

@pytest.fixture
async def db_manager():
    """Create a temporary database for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_vocabulary.db")
    
    # Initialize database manager
    manager = DatabaseManager(db_path)
    
    # Get the schema path
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              "database", "schema.sql")
    
    # Initialize database
    await manager.init_db(schema_path)
    
    yield manager
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)

@pytest.mark.asyncio
async def test_add_word_group(db_manager):
    """Test adding a word group"""
    group_id = await db_manager.add_word_group("Test Group")
    assert group_id > 0

@pytest.mark.asyncio
async def test_add_word(db_manager):
    """Test adding a word"""
    # First add a group
    group_id = await db_manager.add_word_group("Test Group")
    
    # Add a word
    word_data = {
        'kanji': 'テスト',
        'romaji': 'tesuto',
        'english': 'test'
    }
    word_id = await db_manager.add_word(word_data, group_id)
    assert word_id > 0

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
    """Test study session creation and management"""
    # Create a study session
    session_data = {
        'activity_type': 'typing_tutor',
        'group_id': 1,
        'start_time': datetime.now().isoformat()
    }
    session_id = await db_manager.add_study_session(session_data)
    assert session_id > 0

@pytest.mark.asyncio
async def test_database_backup(db_manager):
    """Test database backup functionality"""
    backup_path = await db_manager.backup_database()
    assert os.path.exists(backup_path)
    assert backup_path.endswith('.db')