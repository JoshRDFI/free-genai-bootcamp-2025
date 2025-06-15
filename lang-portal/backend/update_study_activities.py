from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import StudyActivity
import os

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

# Define the correct study activities
activities = [
    {
        "name": "Kanji Writing Practice",
        "description": "Practice writing kanji characters with stroke order guidance and feedback.",
        "thumbnail": "/thumbnails/kanji-writing.png",
        "url": "http://localhost:3000/kanji-writing"
    },
    {
        "name": "Vocabulary Quiz",
        "description": "Test your knowledge of Japanese vocabulary with multiple choice questions.",
        "thumbnail": "/thumbnails/vocab-quiz.png",
        "url": "http://localhost:3000/vocab-quiz"
    },
    {
        "name": "Sentence Construction",
        "description": "Build Japanese sentences by arranging words in the correct order.",
        "thumbnail": "/thumbnails/sentence-construction.png",
        "url": ""
    },
    {
        "name": "Listening Comprehension",
        "description": "Improve your listening skills with audio exercises and comprehension questions.",
        "thumbnail": "/thumbnails/listening.png",
        "url": "http://localhost:3000/listening"
    }
]

# Delete all existing activities
session.query(StudyActivity).delete()

# Add the correct activities
for activity_data in activities:
    activity = StudyActivity(**activity_data)
    session.add(activity)

# Commit the changes
session.commit()
session.close()

print("Study activities updated successfully!") 