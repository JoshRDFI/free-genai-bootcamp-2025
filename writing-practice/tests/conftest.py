import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sqlite3
import json
import yaml

@pytest.fixture(scope="session")
def test_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def test_db(test_dir):
    """Create a test database with sample data"""
    db_path = Path(test_dir) / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            group_id INTEGER,
            kanji TEXT,
            romaji TEXT,
            english TEXT
        )
    """)
    
    # Insert sample data
    cursor.execute("""
        INSERT INTO words (group_id, kanji, romaji, english)
        VALUES (1, '猫', 'neko', 'cat'),
               (1, '犬', 'inu', 'dog'),
               (2, '本', 'hon', 'book')
    """)
    
    conn.commit()
    conn.close()
    return db_path

@pytest.fixture(scope="session")
def test_sentences(test_dir):
    """Create a test sentences file"""
    sentences = [
        {
            "japanese": "猫が好きです。",
            "english": "I like cats.",
            "category": "animals",
            "level": "N5"
        },
        {
            "japanese": "本を読みます。",
            "english": "I read books.",
            "category": "activities",
            "level": "N5"
        }
    ]
    
    sentences_path = Path(test_dir) / "test_sentences.json"
    with open(sentences_path, "w") as f:
        json.dump(sentences, f)
    return sentences_path

@pytest.fixture(scope="session")
def test_prompts(test_dir):
    """Create a test prompts file"""
    prompts = {
        "translation": {
            "system": "You are a Japanese translator.",
            "user": "Translate this text: {text}"
        },
        "grading": {
            "system": "You are a Japanese language teacher.",
            "user": "Grade this submission: {submission}"
        },
        "sentence_generation": {
            "system": "You are a Japanese sentence generator.",
            "user": "Generate a sentence using: {word}"
        }
    }
    
    prompts_path = Path(test_dir) / "test_prompts.yaml"
    with open(prompts_path, "w") as f:
        yaml.dump(prompts, f)
    return prompts_path

@pytest.fixture(scope="session")
def test_config(test_dir, test_db, test_sentences, test_prompts):
    """Create a test configuration"""
    return {
        "base_dir": test_dir,
        "db_path": test_db,
        "sentences_path": test_sentences,
        "prompts_path": test_prompts
    } 