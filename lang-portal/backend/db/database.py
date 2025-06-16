from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Create database engine
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 