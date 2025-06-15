from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')

Base = declarative_base()

class SentenceProgress(Base):
    __tablename__ = "sentence_progress"

    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(String, index=True)
    attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    last_attempted = Column(DateTime, default=datetime.now)
    success_rate = Column(Float, default=0.0)

def main():
    # Create the table
    Base.metadata.create_all(bind=engine)
    print("Added sentence_progress table to the database")

if __name__ == "__main__":
    main() 