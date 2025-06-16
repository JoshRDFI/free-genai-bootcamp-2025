from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.db.database import get_db
from backend.db.models import ListeningExercise, ListeningQuestion
from pydantic import BaseModel

router = APIRouter()

class QuestionBase(BaseModel):
    question_type: str
    question_text: str
    correct_answer: str
    options: List[str]
    points: int

class ListeningExerciseBase(BaseModel):
    title: str
    audio_file: str
    difficulty: str
    description: str

class ListeningExerciseResponse(ListeningExerciseBase):
    id: int
    questions: List[QuestionBase]

    class Config:
        from_attributes = True

@router.get("/exercises", response_model=List[ListeningExerciseResponse])
def get_exercises(db: Session = Depends(get_db)):
    exercises = db.query(ListeningExercise).all()
    return exercises

@router.get("/exercises/{exercise_id}", response_model=ListeningExerciseResponse)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(ListeningExercise).filter(ListeningExercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise 