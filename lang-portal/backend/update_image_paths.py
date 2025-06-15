from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import StudyActivity
import os

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

# Map activity names to their correct thumbnail filenames
thumbnail_map = {
    "Flashcards": "vocab-quiz.png",  # Using vocab-quiz for flashcards
    "Quiz": "vocab-quiz.png",
    "Writing Practice": "kanji-writing.png",
    "Listening Practice": "listening.png",
    "Sentence Construction": "sentence-construction.png"
}

# Get all activities
activities = session.query(StudyActivity).all()

# Update paths to use correct filenames
for activity in activities:
    if activity.name in thumbnail_map:
        activity.thumbnail = f"/thumbnails/{thumbnail_map[activity.name]}"
        print(f"Updated {activity.name}: {activity.thumbnail}")

# Commit changes
session.commit()
print("All paths updated successfully!") 