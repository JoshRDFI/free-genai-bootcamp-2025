import pytest
import asyncio
import os
import tempfile
from src.database import DatabaseManager

@pytest.fixture
async def db_manager():
    """Create a temporary database manager for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Initialize manager
    manager = DatabaseManager(db_path)
    await manager.initialize()
    
    yield manager
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)

@pytest.mark.asyncio
async def test_add_word_group(db_manager):
    """Test adding a word group"""
    group_data = {
        "name": "Test Group",
        "jlpt_level": "N5",
        "description": "Test description"
    }
    
    group_id = await db_manager.add_word_group(group_data)
    assert group_id > 0
    
    # Verify group was added
    group = await db_manager.get_word_group(group_id)
    assert group["name"] == group_data["name"]
    assert group["jlpt_level"] == group_data["jlpt_level"]
    assert group["description"] == group_data["description"]

@pytest.mark.asyncio
async def test_add_word(db_manager):
    """Test adding a word"""
    # First create a group
    group_id = await db_manager.add_word_group({
        "name": "Test Group",
        "jlpt_level": "N5"
    })
    
    word_data = {
        "kanji": "食べる",
        "romaji": "taberu",
        "english": "to eat",
        "group_id": group_id,
        "jlpt_level": "N5"
    }
    
    word_id = await db_manager.add_word(word_data)
    assert word_id > 0
    
    # Verify word was added
    word = await db_manager.get_word(word_id)
    assert word["kanji"] == word_data["kanji"]
    assert word["romaji"] == word_data["romaji"]
    assert word["english"] == word_data["english"]
    assert word["group_id"] == group_id

@pytest.mark.asyncio
async def test_study_session(db_manager):
    """Test study session management"""
    # Create a test user
    user_id = await db_manager.add_user({
        "name": "Test User",
        "current_level": "N5"
    })
    
    # Create a study session
    session_data = {
        "user_id": user_id,
        "activity_type": "typing_tutor",
        "group_id": 1
    }
    
    session_id = await db_manager.create_study_session(session_data)
    assert session_id > 0
    
    # End the session
    await db_manager.end_study_session(session_id)
    
    # Verify session was updated
    session = await db_manager.get_study_session(session_id)
    assert session["end_time"] is not None
    assert session["duration"] >= 0

@pytest.mark.asyncio
async def test_word_review(db_manager):
    """Test word review tracking"""
    # Create a test user and session
    user_id = await db_manager.add_user({
        "name": "Test User",
        "current_level": "N5"
    })
    
    session_id = await db_manager.create_study_session({
        "user_id": user_id,
        "activity_type": "typing_tutor",
        "group_id": 1
    })
    
    # Add a word review
    review_data = {
        "word_id": 1,
        "session_id": session_id,
        "correct": True
    }
    
    review_id = await db_manager.add_word_review(review_data)
    assert review_id > 0
    
    # Verify review was added
    review = await db_manager.get_word_review(review_id)
    assert review["word_id"] == review_data["word_id"]
    assert review["session_id"] == review_data["session_id"]
    assert review["correct"] == review_data["correct"]

@pytest.mark.asyncio
async def test_user_progression(db_manager):
    """Test user progression tracking"""
    # Create a test user
    user_id = await db_manager.add_user({
        "name": "Test User",
        "current_level": "N5"
    })
    
    # Advance user level
    new_level = await db_manager.advance_user_level(user_id, "N4")
    assert new_level == "N4"
    
    # Verify progression history
    history = await db_manager.get_user_progression_history(user_id)
    assert len(history) > 0
    assert history[0]["previous_level"] == "N5"
    assert history[0]["new_level"] == "N4"

@pytest.mark.asyncio
async def test_database_backup(db_manager):
    """Test database backup functionality"""
    # Create a backup
    backup_path = await db_manager.create_backup()
    assert os.path.exists(backup_path)
    
    # Verify backup file size
    assert os.path.getsize(backup_path) > 0
    
    # Cleanup
    os.remove(backup_path)

@pytest.mark.asyncio
async def test_connection_pool(db_manager):
    """Test database connection pool"""
    # Test multiple concurrent operations
    async def test_operation():
        async with db_manager.get_connection() as conn:
            await conn.execute("SELECT 1")
    
    # Run multiple operations concurrently
    tasks = [test_operation() for _ in range(5)]
    await asyncio.gather(*tasks)
    
    # Verify pool is working correctly
    assert db_manager.pool.qsize() == db_manager.pool.maxsize 