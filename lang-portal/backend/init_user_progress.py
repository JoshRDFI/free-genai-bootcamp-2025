from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, UserProgress
import os

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_user_progress():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a new session
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

if __name__ == "__main__":
    init_user_progress() 