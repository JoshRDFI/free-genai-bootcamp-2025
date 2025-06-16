# backend/db/init_db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, StudyActivity, ListeningExercise, ListeningQuestion
import os

# Create database engine
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_listening_exercises():
    db = SessionLocal()
    try:
        # Delete existing exercises
        db.query(ListeningQuestion).delete()
        db.query(ListeningExercise).delete()

        # Create sample exercises
        exercises = [
            ListeningExercise(
                title="Basic Greetings",
                audio_file="/audio/greetings.mp3",
                difficulty="Beginner",
                description="Practice understanding basic Japanese greetings and introductions.",
                questions=[
                    ListeningQuestion(
                        question_type="multiple_choice",
                        question_text="What does the speaker say at the beginning?",
                        correct_answer="こんにちは",
                        options=["こんにちは", "さようなら", "おはよう", "こんばんは"],
                        points=1
                    ),
                    ListeningQuestion(
                        question_type="multiple_choice",
                        question_text="How does the speaker respond to 'お元気ですか'?",
                        correct_answer="はい、元気です",
                        options=["はい、元気です", "いいえ、元気ではありません", "ありがとう", "さようなら"],
                        points=1
                    )
                ]
            ),
            ListeningExercise(
                title="Daily Activities",
                audio_file="/audio/daily_activities.mp3",
                difficulty="Intermediate",
                description="Listen to a conversation about daily routines and activities.",
                questions=[
                    ListeningQuestion(
                        question_type="multiple_choice",
                        question_text="What time does the speaker wake up?",
                        correct_answer="6:00 AM",
                        options=["6:00 AM", "7:00 AM", "8:00 AM", "9:00 AM"],
                        points=1
                    ),
                    ListeningQuestion(
                        question_type="fill_blank",
                        question_text="The speaker goes to work by _____.",
                        correct_answer="train",
                        options=["train", "bus", "car", "bicycle"],
                        points=1
                    )
                ]
            )
        ]

        db.add_all(exercises)
        db.commit()
        print("Created sample listening exercises")
    finally:
        db.close()

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
                        url="http://localhost:5173/quiz"
                    ),
                    StudyActivity(
                        name="Sentence Construction",
                        description="Build Japanese sentences by arranging words in the correct order.",
                        thumbnail="/thumbnails/sentence-construction.png",
                        url="http://localhost:5173/sentence-constructor"
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
    create_listening_exercises() 