# populate_db.py
import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Word, Group, StudyActivity, StudySession, WordReviewItem

# Create the database engine
engine = create_engine("sqlite:///./langportal.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a session
db = SessionLocal()

# Create study activities
activities = [
    StudyActivity(name="Flashcards", url="/flashcards"),
    StudyActivity(name="Quiz", url="/quiz"),
    StudyActivity(name="Writing Practice", url="/writing"),
    StudyActivity(name="Listening Practice", url="/listening")
]

for activity in activities:
    db.add(activity)
db.commit()

# Create word groups
groups = [
    Group(name="Basic Greetings"),
    Group(name="Common Verbs"),
    Group(name="Numbers"),
    Group(name="Time Expressions"),
    Group(name="Basic Adjectives"),
    Group(name="Question Words"),
    Group(name="Family Members"),
    Group(name="Food and Drink")
]

for group in groups:
    db.add(group)
db.commit()

# Create words with proper relationships and parts
words_data = [
    # Basic Greetings
    {
        "kanji": "こんにちは",
        "romaji": "konnichiwa",
        "english": "hello",
        "parts": {"type": "greeting", "usage": "formal", "time": "day"},
        "group": "Basic Greetings"
    },
    {
        "kanji": "おはよう",
        "romaji": "ohayou",
        "english": "good morning",
        "parts": {"type": "greeting", "usage": "casual", "time": "morning"},
        "group": "Basic Greetings"
    },
    {
        "kanji": "こんばんは",
        "romaji": "konbanwa",
        "english": "good evening",
        "parts": {"type": "greeting", "usage": "formal", "time": "evening"},
        "group": "Basic Greetings"
    },
    {
        "kanji": "さようなら",
        "romaji": "sayounara",
        "english": "goodbye",
        "parts": {"type": "farewell", "usage": "formal"},
        "group": "Basic Greetings"
    },
    {
        "kanji": "ありがとう",
        "romaji": "arigatou",
        "english": "thank you",
        "parts": {"type": "expression", "usage": "polite"},
        "group": "Basic Greetings"
    },
    
    # Common Verbs
    {
        "kanji": "食べる",
        "romaji": "taberu",
        "english": "to eat",
        "parts": {"type": "verb", "group": "ru-verb", "usage": "common"},
        "group": "Common Verbs"
    },
    {
        "kanji": "飲む",
        "romaji": "nomu",
        "english": "to drink",
        "parts": {"type": "verb", "group": "u-verb", "usage": "common"},
        "group": "Common Verbs"
    },
    {
        "kanji": "行く",
        "romaji": "iku",
        "english": "to go",
        "parts": {"type": "verb", "group": "u-verb", "usage": "common"},
        "group": "Common Verbs"
    },
    {
        "kanji": "来る",
        "romaji": "kuru",
        "english": "to come",
        "parts": {"type": "verb", "group": "irregular", "usage": "common"},
        "group": "Common Verbs"
    },
    {
        "kanji": "する",
        "romaji": "suru",
        "english": "to do",
        "parts": {"type": "verb", "group": "irregular", "usage": "common"},
        "group": "Common Verbs"
    },
    
    # Numbers
    {
        "kanji": "一",
        "romaji": "ichi",
        "english": "one",
        "parts": {"type": "number", "usage": "basic"},
        "group": "Numbers"
    },
    {
        "kanji": "二",
        "romaji": "ni",
        "english": "two",
        "parts": {"type": "number", "usage": "basic"},
        "group": "Numbers"
    },
    {
        "kanji": "三",
        "romaji": "san",
        "english": "three",
        "parts": {"type": "number", "usage": "basic"},
        "group": "Numbers"
    },
    {
        "kanji": "四",
        "romaji": "yon",
        "english": "four",
        "parts": {"type": "number", "usage": "basic"},
        "group": "Numbers"
    },
    {
        "kanji": "五",
        "romaji": "go",
        "english": "five",
        "parts": {"type": "number", "usage": "basic"},
        "group": "Numbers"
    },
    
    # Time Expressions
    {
        "kanji": "今日",
        "romaji": "kyou",
        "english": "today",
        "parts": {"type": "time", "usage": "common"},
        "group": "Time Expressions"
    },
    {
        "kanji": "明日",
        "romaji": "ashita",
        "english": "tomorrow",
        "parts": {"type": "time", "usage": "common"},
        "group": "Time Expressions"
    },
    {
        "kanji": "昨日",
        "romaji": "kinou",
        "english": "yesterday",
        "parts": {"type": "time", "usage": "common"},
        "group": "Time Expressions"
    },
    {
        "kanji": "今",
        "romaji": "ima",
        "english": "now",
        "parts": {"type": "time", "usage": "common"},
        "group": "Time Expressions"
    },
    {
        "kanji": "毎日",
        "romaji": "mainichi",
        "english": "every day",
        "parts": {"type": "time", "usage": "common"},
        "group": "Time Expressions"
    }
]

# Create words and add them to groups
for word_data in words_data:
    word = Word(
        kanji=word_data["kanji"],
        romaji=word_data["romaji"],
        english=word_data["english"],
        parts=word_data["parts"]
    )
    db.add(word)
    db.flush()  # Flush to get the word ID
    
    # Find the corresponding group
    group = next(g for g in groups if g.name == word_data["group"])
    word.groups.append(group)
    
    # Update the group's words_count
    group.words_count = len(group.words) + 1

db.commit()

# Create a sample study session
session = StudySession(
    group_id=groups[0].id,  # Using the first group (Basic Greetings)
    study_activity_id=activities[0].id  # Using Flashcards activity
)
db.add(session)
db.commit()

# Create some sample review items
for word in groups[0].words[:3]:  # Review first 3 words from Basic Greetings
    review = WordReviewItem(
        word_id=word.id,
        study_session_id=session.id,
        correct=True
    )
    db.add(review)

db.commit()

# Close the session
db.close()

print("Database populated successfully!")