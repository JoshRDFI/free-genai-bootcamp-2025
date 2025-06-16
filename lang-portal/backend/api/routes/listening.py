from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.db.database import get_db
from backend.db.models import ListeningExercise, ListeningQuestion
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class QuestionBase(BaseModel):
    id: int
    question_type: str
    question_text: str
    correct_answer: str
    options: List[str]
    points: int

    class Config:
        from_attributes = True

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

class UserAnswer(BaseModel):
    question_id: int
    answer: str

class ListeningAttempt(BaseModel):
    score: float
    total_questions: int

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

@router.post("/exercises/{exercise_id}/submit", response_model=ListeningAttempt)
def submit_answers(exercise_id: int, answers: List[UserAnswer], db: Session = Depends(get_db)):
    try:
        logger.info(f"Received submission for exercise {exercise_id}")
        logger.info(f"Answers received: {answers}")

        exercise = db.query(ListeningExercise).filter(ListeningExercise.id == exercise_id).first()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Get all questions for this exercise
        questions = exercise.questions
        logger.info(f"Exercise questions: {[q.id for q in questions]}")

        # Validate that we have answers for all questions
        if len(answers) != len(questions):
            raise HTTPException(
                status_code=422,
                detail=f"Expected {len(questions)} answers but received {len(answers)}"
            )

        # Validate that all question IDs are valid
        question_ids = {q.id for q in questions}
        answer_ids = {a.question_id for a in answers}
        if not answer_ids.issubset(question_ids):
            invalid_ids = answer_ids - question_ids
            raise HTTPException(
                status_code=422,
                detail=f"Invalid question IDs received: {invalid_ids}"
            )

        total_questions = len(questions)
        correct_answers = 0

        # Check each answer
        for answer in answers:
            question = next((q for q in questions if q.id == answer.question_id), None)
            if question and answer.answer == question.correct_answer:
                correct_answers += 1

        # Calculate score as percentage
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        logger.info(f"Submission successful. Score: {score}%")
        return ListeningAttempt(
            score=score,
            total_questions=total_questions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 