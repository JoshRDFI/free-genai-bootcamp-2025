# backend/db/init_db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, StudyActivity
from backend.api.main import app
import os

# Create database engine
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Check if database exists
    if not os.path.exists(db_path):
        # Create all tables only if database doesn't exist
        Base.metadata.create_all(bind=engine)

        # Create a new session
        db = SessionLocal()

        try:
            # Add sample study activities if none exist
            if db.query(StudyActivity).count() == 0:
                activities = [
                    StudyActivity(
                        name="Kanji Writing Practice",
                        description="Practice writing kanji characters with stroke order guidance and feedback.",
                        thumbnail="/thumbnails/kanji-writing.png",
                        url="http://localhost:5173/kanji-writing"
                    ),
                    StudyActivity(
                        name="Vocabulary Quiz",
                        description="Test your knowledge of Japanese vocabulary with multiple choice questions.",
                        thumbnail="/thumbnails/vocab-quiz.png",
                        url="http://localhost:5173/vocab-quiz"
                    ),
                    StudyActivity(
                        name="Sentence Construction",
                        description="Build Japanese sentences by arranging words in the correct order.",
                        thumbnail="/thumbnails/sentence-construction.png",
                        url="http://localhost:5173/sentence-construction"
                    ),
                    StudyActivity(
                        name="Listening Comprehension",
                        description="Improve your listening skills with audio exercises and comprehension questions.",
                        thumbnail="/thumbnails/listening.png",
                        url="http://localhost:5173/listening"
                    )
                ]
                db.add_all(activities)
                db.commit()
        finally:
            db.close()
    else:
        print(f"Database already exists at {db_path}")

if __name__ == '__main__':
    init_db() 