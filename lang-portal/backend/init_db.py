import os
import sys
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declarative_base

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define models
class StudyActivity(Base):
    __tablename__ = "study_activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    thumbnail = Column(String)
    url = Column(String)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    words_count = Column(Integer, default=0)

class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    kanji = Column(String, index=True)
    romaji = Column(String)
    english = Column(String)
    parts = Column(JSON)

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer)
    study_activity_id = Column(Integer)
    quiz_metadata = Column(JSON, default={})

class WordReviewItem(Base):
    __tablename__ = "word_review_items"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer)
    study_session_id = Column(Integer)
    correct = Column(Integer)

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    current_level = Column(String, default='N5')

class SentenceProgress(Base):
    __tablename__ = "sentence_progress"
    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(String, index=True)
    attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    last_attempted = Column(DateTime, default=datetime.now)
    success_rate = Column(Float, default=0.0)

# Sample stroke data for some common kanji
STROKE_DATA = {
    "一": {
        "strokes": 1,
        "strokeOrder": [
            {"points": [[0.2, 0.5], [0.8, 0.5]]}
        ]
    },
    "二": {
        "strokes": 2,
        "strokeOrder": [
            {"points": [[0.2, 0.3], [0.8, 0.3]]},
            {"points": [[0.2, 0.7], [0.8, 0.7]]}
        ]
    },
    "三": {
        "strokes": 3,
        "strokeOrder": [
            {"points": [[0.2, 0.2], [0.8, 0.2]]},
            {"points": [[0.2, 0.5], [0.8, 0.5]]},
            {"points": [[0.2, 0.8], [0.8, 0.8]]}
        ]
    },
    "四": {
        "strokes": 5,
        "strokeOrder": [
            {"points": [[0.2, 0.2], [0.8, 0.2]]},
            {"points": [[0.2, 0.2], [0.2, 0.8]]},
            {"points": [[0.2, 0.8], [0.8, 0.8]]},
            {"points": [[0.8, 0.2], [0.8, 0.8]]},
            {"points": [[0.3, 0.5], [0.7, 0.5]]}
        ]
    },
    "五": {
        "strokes": 4,
        "strokeOrder": [
            {"points": [[0.2, 0.2], [0.8, 0.2]]},
            {"points": [[0.2, 0.2], [0.2, 0.8]]},
            {"points": [[0.2, 0.8], [0.8, 0.8]]},
            {"points": [[0.3, 0.5], [0.7, 0.5]]}
        ]
    }
}

def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Created all database tables")

def create_study_activities():
    db = SessionLocal()
    try:
        # Define the study activities
        activities = [
            {
                "name": "Kanji Writing Practice",
                "description": "Practice writing kanji characters with stroke order guidance and feedback.",
                "thumbnail": "/thumbnails/kanji-writing.png",
                "url": "http://localhost:5173/kanji-writing"
            },
            {
                "name": "Vocabulary Quiz",
                "description": "Test your knowledge of Japanese vocabulary with multiple choice questions.",
                "thumbnail": "/thumbnails/vocab-quiz.png",
                "url": "http://localhost:5173/vocab-quiz"
            },
            {
                "name": "Sentence Construction",
                "description": "Build Japanese sentences by arranging words in the correct order.",
                "thumbnail": "/thumbnails/sentence-construction.png",
                "url": "http://localhost:5173/sentence-construction"
            },
            {
                "name": "Listening Comprehension",
                "description": "Improve your listening skills with audio exercises and comprehension questions.",
                "thumbnail": "/thumbnails/listening.png",
                "url": "http://localhost:5173/listening"
            }
        ]

        # Delete existing activities
        db.query(StudyActivity).delete()

        # Add new activities
        for activity_data in activities:
            activity = StudyActivity(**activity_data)
            db.add(activity)

        db.commit()
        print("Created study activities")
    finally:
        db.close()

def init_user_progress():
    db = SessionLocal()
    try:
        # Add initial user progress if none exists
        if db.query(UserProgress).count() == 0:
            progress = UserProgress(current_level='N5')
            db.add(progress)
            db.commit()
            print("Initialized user progress with N5 level")
        else:
            print("User progress already exists")
    finally:
        db.close()

def populate_words_from_json():
    db = SessionLocal()
    try:
        # Read words from JSON file
        words_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src', 'data', 'words.json')
        with open(words_json_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)

        # Create groups based on unique categories
        groups = {}
        for word in words_data:
            category = word['category']
            if category not in groups:
                group = Group(name=category)
                db.add(group)
                db.flush()  # Flush to get the group ID
                groups[category] = group

        db.commit()

        # Create words and add them to groups
        for word_data in words_data:
            word = Word(
                kanji=word_data["kanji"],
                romaji=word_data["romaji"],
                english=word_data["english"],
                parts={"level": word_data["level"]}  # Store level in parts
            )
            db.add(word)
            db.flush()  # Flush to get the word ID
            
            # Find the corresponding group
            group = groups[word_data["category"]]
            word.groups.append(group)
            
            # Update the group's words_count
            group.words_count = len(group.words) + 1

        db.commit()
        print("Populated words from JSON")
    finally:
        db.close()

def update_stroke_data():
    db = SessionLocal()
    try:
        # Get all words
        words = db.query(Word).all()

        for word in words:
            # Add stroke data if available
            if word.kanji in STROKE_DATA:
                parts = word.parts or {}
                parts.update(STROKE_DATA[word.kanji])
                word.parts = parts
            else:
                # For kanji without stroke data, add placeholder
                parts = word.parts or {}
                parts.update({
                    "strokes": 0,
                    "strokeOrder": []
                })
                word.parts = parts

        db.commit()
        print("Updated stroke data for all words")
    finally:
        db.close()

def create_sample_study_session():
    db = SessionLocal()
    try:
        # Get the first group and activity
        first_group = db.query(Group).first()
        first_activity = db.query(StudyActivity).first()

        if first_group and first_activity:
            # Create a sample study session
            session = StudySession(
                group_id=first_group.id,
                study_activity_id=first_activity.id
            )
            db.add(session)
            db.commit()

            # Create some sample review items
            for word in first_group.words[:3]:  # Review first 3 words
                review = WordReviewItem(
                    word_id=word.id,
                    study_session_id=session.id,
                    correct=True
                )
                db.add(review)

            db.commit()
            print("Created sample study session")
    finally:
        db.close()

def main():
    print("Starting database initialization...")
    
    # Initialize database structure
    init_database()
    
    # Create study activities
    create_study_activities()
    
    # Initialize user progress
    init_user_progress()
    
    # Populate words from JSON
    populate_words_from_json()
    
    # Update stroke data
    update_stroke_data()
    
    # Create sample study session
    create_sample_study_session()
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    main() 