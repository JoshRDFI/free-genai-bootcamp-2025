import pytest
import asyncio
import os
import tempfile
import aiosqlite # Added for manual schema execution
import json
from datetime import datetime
from src.database import DatabaseManager

@pytest.fixture
async def db_manager():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_vocabulary.db")
    
    manager = DatabaseManager(db_path)
    
    # Manually apply schema
    # schema.sql path is PROJECT_ROOT/data/shared_db/schema.sql
    # __file__ is vocabulary_generator/tests/test_database.py
    # project_root is two levels up from __file__'s parent
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schema_path = os.path.join(project_root, "data", "shared_db", "schema.sql")

    async with aiosqlite.connect(db_path) as db:
        with open(schema_path, 'r') as f:
            await db.executescript(f.read())
        await db.commit()
        
    # Initialize connection pool in manager (does not apply schema)
    await manager.init_db() 
    
    yield manager
    
    # Cleanup: Close connections in pool before removing file
    while not manager.pool.empty():
        conn = await manager.pool.get()
        await conn.close()

    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)

@pytest.mark.asyncio
async def test_add_word_group(db_manager):
    """Test adding a word group"""
    group_id = await db_manager.add_word_group("Test Group")
    assert group_id > 0
    group = await db_manager.get_all_word_groups() # Check if it's there
    assert any(g['name'] == "Test Group" for g in group)

@pytest.mark.asyncio
async def test_add_word_and_association(db_manager):
    """Test adding a word and associating it with a group"""
    group_name = "Verb Group"
    group_id = await db_manager.add_word_group(group_name)
    assert group_id > 0
    
    word_data_to_add = {
        'kanji': '食べる',
        'romaji': 'taberu',
        'english': 'to eat',
        'parts': '{"type": "verb"}', # parts is a JSON string
        'group_id': group_id  # For the legacy words.group_id column
    }
    word_id = await db_manager.add_word(word_data_to_add)
    assert word_id > 0

    # Test associating the word with the group
    await db_manager.add_word_to_group(word_id, group_id)

    # Verify association
    words_in_group = await db_manager.get_words_by_group(group_id)
    assert len(words_in_group) == 1
    assert words_in_group[0]['id'] == word_id
    assert words_in_group[0]['kanji'] == '食べる'
    assert json.loads(words_in_group[0]['parts'])['type'] == 'verb'

    groups_for_word = await db_manager.get_groups_for_word(word_id)
    assert len(groups_for_word) == 1
    assert groups_for_word[0]['id'] == group_id
    assert groups_for_word[0]['name'] == group_name
    
    # Check words_count in word_groups table (via get_all_word_groups)
    all_groups = await db_manager.get_all_word_groups()
    target_group_info = next((g for g in all_groups if g['id'] == group_id), None)
    assert target_group_info is not None
    assert target_group_info['words_count'] == 1
    
    retrieved_word = await db_manager.get_word(word_id)
    assert retrieved_word is not None
    assert retrieved_word['parts'] == '{"type": "verb"}'
    assert retrieved_word['legacy_group_id'] == group_id

@pytest.mark.asyncio
async def test_word_validation(db_manager):
    """Test word data validation"""
    group_id = await db_manager.add_word_group("Validation Group")
    
    # Test missing required field (e.g., english)
    with pytest.raises(ValueError, match="Missing required fields"):
        await db_manager.add_word({
            'kanji': 'テスト', 
            'romaji': 'tesuto',
            # 'english': 'test', Missing
            'parts': '{}', 
            'group_id': group_id
        })
    
    # Test empty string for kanji
    with pytest.raises(ValueError, match="Kanji must be a non-empty string"):
        await db_manager.add_word({
            'kanji': '', 
            'romaji': 'tesuto', 
            'english': 'test', 
            'parts': '{}', 
            'group_id': group_id
        })

    # Test parts not a string
    with pytest.raises(ValueError, match="Parts must be a string"):
        await db_manager.add_word({
            'kanji': 'テスト', 
            'romaji': 'tesuto', 
            'english': 'test', 
            'parts': {}, # Should be JSON string
            'group_id': group_id
        })

    # Test parts not valid JSON string
    with pytest.raises(ValueError, match="Parts must be a valid JSON string"):
        await db_manager.add_word({
            'kanji': 'テスト', 
            'romaji': 'tesuto', 
            'english': 'test', 
            'parts': 'not valid json', 
            'group_id': group_id
        })
    
    # Test group_id not an int
    with pytest.raises(ValueError, match="group_id must be an integer"):
        await db_manager.add_word({
            'kanji': 'テスト', 
            'romaji': 'tesuto', 
            'english': 'test', 
            'parts': '{}', 
            'group_id': "not_an_int"
        })

@pytest.mark.asyncio
async def test_study_session(db_manager):
    """Test study session creation and management"""
    # First, ensure a group and user exist for the session
    group_id = await db_manager.add_word_group("Session Group")
    # Assuming default user ID 1 will be used by ensure_default_user_exists or similar
    # For this isolated test, ensure the user exists if your add_study_session requires valid user_id from users table
    try:
        await db_manager.add_user({'id': 1, 'name': 'Test User', 'current_level': 'N5'})
    except Exception: # User might already exist if schema adds a default one.
        pass

    session_data = {
        'activity_type': 'typing_tutor',
        'group_id': group_id, # Use created group_id
        'user_id': 1, # Assuming user_id 1
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(), # add_study_session expects this
        'duration': 0, # add_study_session expects this
        'accuracy': 0.0 # add_study_session expects this
    }
    session_id = await db_manager.add_study_session(session_data)
    assert session_id > 0

@pytest.mark.asyncio
async def test_database_backup(db_manager):
    """Test database backup functionality"""
    # Ensure db file exists by adding some data
    await db_manager.add_word_group("Backup Test Group")

    backup_path = await db_manager.backup_database()
    assert backup_path is not None
    assert os.path.exists(backup_path)
    assert backup_path.endswith('.db')