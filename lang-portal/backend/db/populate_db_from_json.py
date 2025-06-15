import os
import sys
import json
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
    StudyActivity(
        name="Flashcards",
        description="Practice vocabulary with flashcards",
        thumbnail="/thumbnails/flashcards.jpg",
        url="/flashcards"
    ),
    StudyActivity(
        name="Quiz",
        description="Test your knowledge with quizzes",
        thumbnail="/thumbnails/quiz.jpg",
        url="/quiz"
    ),
    StudyActivity(
        name="Writing Practice",
        description="Practice writing Japanese characters",
        thumbnail="/thumbnails/writing.jpg",
        url="/writing"
    ),
    StudyActivity(
        name="Listening Practice",
        description="Improve your listening skills",
        thumbnail="/thumbnails/listening.jpg",
        url="/listening"
    )
]

for activity in activities:
    db.add(activity)
db.commit()

# Read words from JSON file
words_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'src', 'data', 'words.json')
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

# Create a sample study session
session = StudySession(
    group_id=list(groups.values())[0].id,  # Using the first group
    study_activity_id=activities[0].id  # Using Flashcards activity
)
db.add(session)
db.commit()

# Create some sample review items
for word in list(groups.values())[0].words[:3]:  # Review first 3 words from first group
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