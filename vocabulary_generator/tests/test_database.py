import pytest
import asyncio
from src.database import DatabaseManager

@pytest.fixture
def db_manager():
    return DatabaseManager(db_path="test_vocabulary.db")

@pytest.mark.asyncio
async def test_add_word_group(db_manager):
    await db_manager.init_db()
    group_id = await db_manager.add_word_group("Test Group")
    assert group_id > 0

@pytest.mark.asyncio
async def test_add_word(db_manager):
    await db_manager.init_db()
    group_id = await db_manager.add_word_group("Test Group")
    word_data = {
        "kanji": "食べる",
        "romaji": "taberu",
        "english": "to eat"
    }
    word_id = await db_manager.add_word(word_data, group_id)
    assert word_id > 0