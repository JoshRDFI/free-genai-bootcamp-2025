#!/usr/bin/env python3
"""
Script to create the Visual Novel database with all required tables and initial data.
"""

import sqlite3
import os
from datetime import datetime

# Database path - should match what the server expects
DB_PATH = "data/shared_db/visual_novel.db"

def create_database():
    """Create the visual novel database with all tables and initial data"""
    
    # Ensure the directory exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created directory: {db_dir}")
    
    # Connect to database (this will create it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Creating database at: {DB_PATH}")
    
    # Create users table
    print("Creating users table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Create progress table
    print("Creating progress table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        lesson_id TEXT NOT NULL,
        scene_id TEXT NOT NULL,
        completed BOOLEAN DEFAULT 0,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, lesson_id, scene_id)
    )
    ''')
    
    # Create vocabulary table
    print("Creating vocabulary table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        japanese TEXT NOT NULL,
        reading TEXT,
        english TEXT,
        lesson_id TEXT,
        mastery_level INTEGER DEFAULT 0,
        last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Insert default user
    print("Inserting default user...")
    try:
        cursor.execute('''
        INSERT INTO users (username, email, created_at) 
        VALUES (?, ?, ?)
        ''', ('Student', 'student@example.com', datetime.now()))
        default_user_id = cursor.lastrowid
        print(f"Created default user with ID: {default_user_id}")
    except sqlite3.IntegrityError:
        print("Default user already exists")
        # Get the existing user ID
        cursor.execute('SELECT id FROM users WHERE username = ?', ('Student',))
        default_user_id = cursor.fetchone()[0]
        print(f"Using existing user with ID: {default_user_id}")
    
    # Insert some initial progress data
    print("Inserting initial progress data...")
    initial_progress = [
        (default_user_id, 'lesson1', 'intro', False),
        (default_user_id, 'lesson1', 'greetings', False),
        (default_user_id, 'lesson2', 'intro', False),
        (default_user_id, 'lesson3', 'intro', False),
    ]
    
    for progress_item in initial_progress:
        try:
            cursor.execute('''
            INSERT INTO progress (user_id, lesson_id, scene_id, completed, last_accessed)
            VALUES (?, ?, ?, ?, ?)
            ''', progress_item + (datetime.now(),))
        except sqlite3.IntegrityError:
            print(f"Progress record already exists for {progress_item[1]}/{progress_item[2]}")
    
    # Insert some initial vocabulary
    print("Inserting initial vocabulary...")
    initial_vocabulary = [
        (default_user_id, 'こんにちは', 'konnichiwa', 'Hello/Good afternoon', 'lesson1'),
        (default_user_id, 'おはようございます', 'ohayou gozaimasu', 'Good morning', 'lesson1'),
        (default_user_id, 'さようなら', 'sayounara', 'Goodbye', 'lesson1'),
        (default_user_id, 'ありがとう', 'arigatou', 'Thank you', 'lesson1'),
        (default_user_id, 'どういたしまして', 'dou itashimashite', "You're welcome", 'lesson1'),
    ]
    
    for vocab_item in initial_vocabulary:
        try:
            cursor.execute('''
            INSERT INTO vocabulary (user_id, japanese, reading, english, lesson_id, mastery_level, last_reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', vocab_item + (0, datetime.now()))
        except sqlite3.IntegrityError:
            print(f"Vocabulary item already exists: {vocab_item[1]}")
    
    # Commit all changes
    conn.commit()
    
    # Verify the tables were created
    print("\nVerifying database structure...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables created:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Show some sample data
    print("\nSample data:")
    
    print("\nUsers:")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
    
    print("\nProgress:")
    cursor.execute("SELECT * FROM progress LIMIT 3")
    progress = cursor.fetchall()
    for prog in progress:
        print(f"  - User: {prog[1]}, Lesson: {prog[2]}, Scene: {prog[3]}, Completed: {prog[4]}")
    
    print("\nVocabulary:")
    cursor.execute("SELECT * FROM vocabulary LIMIT 3")
    vocab = cursor.fetchall()
    for v in vocab:
        print(f"  - Japanese: {v[2]}, Reading: {v[3]}, English: {v[4]}")
    
    conn.close()
    print(f"\nDatabase created successfully at: {DB_PATH}")
    print("Database is ready for the Visual Novel application!")

if __name__ == "__main__":
    create_database() 