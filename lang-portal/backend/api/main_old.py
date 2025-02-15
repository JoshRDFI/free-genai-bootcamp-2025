# api/main.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base, Word, WordGroup, StudySession
from pydantic import BaseModel
import logging

app = FastAPI()
engine = create_engine("sqlite:///./langportal.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Response models
class WordResponse(BaseModel):
    id: int
    kanji: str
    romaji: str
    english: str
    group_id: int
    correct_count: int
    wrong_count: int

class StudySessionResponse(BaseModel):
    id: int
    activity_type: str
    group_id: int
    duration: int
    start_time: str
    end_time: str
    accuracy: float

class WordGroupResponse(BaseModel):
    id: int
    name: str

# Words endpoints
@app.get("/words", response_model=dict)
async def get_words(page: int = 1, per_page: int = 50, sort_by: str = "kanji", order: str = "asc", db: Session = Depends(get_db)):
    try:
        query = db.query(Word)
        order_func = asc if order == "asc" else desc
        total_count = query.count()
        words = query.order_by(order_func(sort_by)) \
                     .offset((page-1) * per_page) \
                     .limit(per_page).all()
        return {"data": [WordResponse.from_orm(word) for word in words], "page": page, "total_pages": (total_count + per_page - 1) // per_page}
    except Exception as e:
        logging.error(f"Error fetching words: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Sessions endpoints
@app.get("/sessions", response_model=dict)
async def get_sessions(page: int = 1, per_page: int = 25, db: Session = Depends(get_db)):
    try:
        query = db.query(StudySession)
        total_count = query.count()
        sessions = query.offset((page-1) * per_page) \
                        .limit(per_page).all()
        return {"data": [StudySessionResponse.from_orm(session) for session in sessions], "page": page, "total_pages": (total_count + per_page - 1) // per_page}
    except Exception as e:
        logging.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Word Groups endpoints
@app.get("/word-groups", response_model=dict)
async def get_word_groups(page: int = 1, per_page: int = 25, db: Session = Depends(get_db)):
    try:
        query = db.query(WordGroup)
        total_count = query.count()
        groups = query.offset((page-1) * per_page) \
                     .limit(per_page).all()
        return {"data": [WordGroupResponse.from_orm(group) for group in groups], "page": page, "total_pages": (total_count + per_page - 1) // per_page}
    except Exception as e:
        logging.error(f"Error fetching word groups: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")