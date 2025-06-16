from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import StudyActivity
import os

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Database URL - now pointing to the correct location
DATABASE_URL = f"sqlite:///{os.path.join(BACKEND_DIR, 'langportal.db')}"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_urls():
    db = SessionLocal()
    try:
        # Update each activity's URL
        activities = db.query(StudyActivity).all()
        for activity in activities:
            if activity.name == "Kanji Writing Practice":
                activity.url = "http://localhost:5173/kanji-writing"
            elif activity.name == "Vocabulary Quiz":
                activity.url = "http://localhost:5173/quiz"
            elif activity.name == "Sentence Construction":
                activity.url = "http://localhost:5173/sentence-constructor"
            elif activity.name == "Listening Comprehension":
                activity.url = "http://localhost:5173/listening"
        
        db.commit()
        print("Updated URLs in the database")
    finally:
        db.close()

if __name__ == "__main__":
    update_urls() 