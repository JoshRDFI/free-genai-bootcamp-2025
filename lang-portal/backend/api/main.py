# backend/api/main.py

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from backend.db.models import Base, Word, Group, StudySession, WordReviewItem, StudyActivity, UserProgress, SentenceProgress as SentenceProgressModel
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import os
import random
from datetime import datetime

T = TypeVar('T')

# Create database engine
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'langportal.db')
print(f"Using database at: {db_path}")

engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
thumbnails_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'thumbnails')
app.mount("/thumbnails", StaticFiles(directory=thumbnails_path), name="thumbnails")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Base Pydantic models
class StudyActivityBase(BaseModel):
    name: str
    description: str
    thumbnail: str
    url: str

class WordBase(BaseModel):
    kanji: str
    romaji: str
    english: str
    parts: dict
    correct_count: int
    wrong_count: int

class GroupBase(BaseModel):
    name: str
    words_count: int

# Response models
class StudyActivityResponse(StudyActivityBase):
    id: int

    class Config:
        from_attributes = True

class WordResponse(WordBase):
    id: int

    class Config:
        from_attributes = True

class GroupResponse(GroupBase):
    id: int

    class Config:
        from_attributes = True

class WordReviewItemResponse(BaseModel):
    id: int
    word_id: int
    study_session_id: int
    correct: bool
    created_at: str
    word: WordResponse

    class Config:
        from_attributes = True

class StudySessionResponse(BaseModel):
    id: int
    group_id: int
    study_activity_id: int
    created_at: str
    updated_at: str
    group: GroupResponse
    study_activity: StudyActivityResponse
    review_items: List[WordReviewItemResponse]
    quiz_metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationInfo

    class Config:
        from_attributes = True

# Quiz-related Pydantic models
class QuizQuestion(BaseModel):
    id: int
    word_id: int
    question_type: str  # "japanese_to_english" or "english_to_japanese"
    question: str
    correct_answer: str
    options: List[str]

class QuizSession(BaseModel):
    id: int
    questions: List[QuizQuestion]
    current_question_index: int = 0
    completed: bool = False

class QuizAnswer(BaseModel):
    question_id: int
    selected_answer: str

class QuizResult(BaseModel):
    correct_count: int
    total_questions: int
    review_items: List[WordReviewItemResponse]

class QuizStartRequest(BaseModel):
    group_id: int

class UserProgressResponse(BaseModel):
    id: int
    current_level: str
    created_at: str
    updated_at: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Sentence Constructor Pydantic models
class SentencePart(BaseModel):
    id: str
    text: str
    type: str
    is_required: bool
    position_hint: str
    grammar_notes: str

class Sentence(BaseModel):
    id: str
    jlpt_level: str
    category: str
    source_language: dict
    target_language: dict
    sentence_parts: dict
    exercises: List[dict]
    metadata: dict

class SentenceAttempt(BaseModel):
    sentence_id: str
    constructed_sentence: str
    is_correct: bool
    time_taken: float

class SentenceProgress(BaseModel):
    sentence_id: str
    attempts: int
    correct_attempts: int
    last_attempted: datetime
    success_rate: float

# Routes
@api_router.get("/study-activities", response_model=List[StudyActivityResponse])
def get_study_activities(db: Session = Depends(get_db)):
    activities = db.query(StudyActivity).all()
    return activities

@api_router.get("/study-activities/{id}", response_model=StudyActivityResponse)
def get_study_activity(id: int, db: Session = Depends(get_db)):
    activity = db.query(StudyActivity).get(id)
    if not activity:
        raise HTTPException(status_code=404, detail="Study activity not found")
    return activity

@api_router.get("/words", response_model=List[WordResponse])
def get_words(
    page: int = 1,
    sort_by: str = "kanji",
    order: str = "asc",
    db: Session = Depends(get_db)
):
    query = db.query(Word)
    if sort_by:
        if order == "asc":
            query = query.order_by(getattr(Word, sort_by).asc())
        else:
            query = query.order_by(getattr(Word, sort_by).desc())
    return query.offset((page - 1) * 50).limit(50).all()

@api_router.get("/user-progress", response_model=UserProgressResponse)
def get_user_progress(db: Session = Depends(get_db)):
    progress = db.query(UserProgress).first()
    if not progress:
        # Create initial progress if none exists
        progress = UserProgress(current_level='N5')
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress.to_dict()

@api_router.put("/user-progress", response_model=UserProgressResponse)
def update_user_progress(level: str, db: Session = Depends(get_db)):
    progress = db.query(UserProgress).first()
    if not progress:
        progress = UserProgress(current_level=level)
        db.add(progress)
    else:
        progress.current_level = level
    db.commit()
    db.refresh(progress)
    return progress.to_dict()

@api_router.get("/api/user-progress", response_model=UserProgressResponse)
def read_user_progress(db: Session = Depends(get_db)):
    progress = get_user_progress(db)
    return progress

@api_router.get("/groups", response_model=PaginatedResponse[GroupResponse])
def get_groups(
    page: int = 1,
    sort_by: str = 'name',
    order: str = 'asc',
    db: Session = Depends(get_db)
):
    # Get user's current level
    progress = db.query(UserProgress).first()
    if not progress:
        progress = UserProgress(current_level='N5')
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    # Define level order for comparison
    level_order = {'N5': 1, 'N4': 2, 'N3': 3, 'N2': 4, 'N1': 5}
    user_level_num = level_order[progress.current_level]
    
    # Build query
    query = db.query(Group)
    
    # Filter groups based on user's level
    filtered_groups = []
    for group in query.all():
        # Get the highest level word in the group
        group_levels = [word.parts.get('level', 'N5') for word in group.words]
        if group_levels:
            highest_level = max(group_levels, key=lambda x: level_order.get(x, 0))
            if level_order[highest_level] <= user_level_num:
                filtered_groups.append(group)
    
    # Sort the filtered groups
    if sort_by == 'name':
        filtered_groups.sort(key=lambda x: x.name, reverse=(order == 'desc'))
    elif sort_by == 'words_count':
        filtered_groups.sort(key=lambda x: x.words_count, reverse=(order == 'desc'))
    
    # Paginate
    total_items = len(filtered_groups)
    items_per_page = 50
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    return {
        "items": filtered_groups[start_idx:end_idx],
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "items_per_page": items_per_page
        }
    }

@api_router.get("/groups/{id}", response_model=GroupResponse)
def get_group(id: int, db: Session = Depends(get_db)):
    group = db.query(Group).get(id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@api_router.get("/sessions", response_model=PaginatedResponse[StudySessionResponse])
def get_sessions(
    page: int = 1,
    db: Session = Depends(get_db)
):
    query = db.query(StudySession).order_by(StudySession.created_at.desc())
    total_items = query.count()
    items_per_page = 50
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    sessions = query.offset((page - 1) * items_per_page).limit(items_per_page).all()
    
    return {
        "items": sessions,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "items_per_page": items_per_page
        }
    }

@api_router.post("/study_sessions", response_model=StudySessionResponse)
def create_study_session(
    group_id: int,
    study_activity_id: int,
    db: Session = Depends(get_db)
):
    session = StudySession(group_id=group_id, study_activity_id=study_activity_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@api_router.post("/study_sessions/{id}/review", response_model=WordReviewItemResponse)
def log_review(
    id: int,
    word_id: int,
    correct: bool,
    db: Session = Depends(get_db)
):
    session = db.query(StudySession).get(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    review = WordReviewItem(word_id=word_id, study_session_id=session.id, correct=correct)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@api_router.post("/quiz/start", response_model=QuizSession)
def start_quiz(
    request: QuizStartRequest,
    db: Session = Depends(get_db)
):
    # Get 5 random words from the group
    words = db.query(Word).join(Word.groups).filter(Group.id == request.group_id).all()
    if len(words) < 5:
        raise HTTPException(status_code=400, detail="Not enough words in the group")
    
    selected_words = random.sample(words, 5)
    
    # Create a study session
    session = StudySession(
        group_id=request.group_id,
        study_activity_id=2  # Quiz activity ID
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Generate questions
    questions = []
    for word in selected_words:
        # Randomly choose question type
        question_type = random.choice(["japanese_to_english", "english_to_japanese"])
        
        if question_type == "japanese_to_english":
            question = f"{word.kanji} ({word.romaji})"
            correct_answer = word.english
            # Get 3 random wrong answers
            wrong_answers = random.sample([w.english for w in words if w.id != word.id], 3)
        else:
            question = word.english
            correct_answer = f"{word.kanji} ({word.romaji})"
            # Get 3 random wrong answers
            wrong_answers = random.sample([f"{w.kanji} ({w.romaji})" for w in words if w.id != word.id], 3)
        
        # Combine and shuffle options
        options = [correct_answer] + wrong_answers
        random.shuffle(options)
        
        questions.append(QuizQuestion(
            id=len(questions) + 1,
            word_id=word.id,
            question_type=question_type,
            question=question,
            correct_answer=correct_answer,
            options=options
        ))
    
    # Store questions in session metadata
    session.quiz_metadata = {
        "questions": [q.dict() for q in questions],
        "current_question_index": 0,
        "completed": False
    }
    db.commit()
    
    return QuizSession(
        id=session.id,
        questions=questions,
        current_question_index=0,
        completed=False
    )

@api_router.post("/quiz/{session_id}/submit", response_model=QuizResult)
def submit_quiz_answer(
    session_id: int,
    answer: QuizAnswer,
    db: Session = Depends(get_db)
):
    session = db.query(StudySession).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get questions from session metadata
    questions = [QuizQuestion(**q) for q in session.quiz_metadata.get("questions", [])]
    
    # Get the question from the session
    question = next((q for q in questions if q.id == answer.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if answer is correct
    is_correct = answer.selected_answer == question.correct_answer
    
    # Create review item
    review = WordReviewItem(
        word_id=question.word_id,
        study_session_id=session_id,
        correct=is_correct
    )
    db.add(review)
    
    # Update word stats
    word = db.query(Word).get(question.word_id)
    if is_correct:
        word.correct_count += 1
    else:
        word.wrong_count += 1
    
    db.commit()
    db.refresh(review)
    
    # Get all review items for this session
    review_items = db.query(WordReviewItem).filter_by(study_session_id=session_id).all()
    
    # Count correct answers
    correct_count = sum(1 for item in review_items if item.correct)
    
    # Convert review items to the expected format
    formatted_review_items = []
    for item in review_items:
        word = db.query(Word).get(item.word_id)
        formatted_review_items.append({
            'id': item.id,
            'word_id': item.word_id,
            'study_session_id': item.study_session_id,
            'correct': item.correct,
            'created_at': item.created_at.isoformat(),
            'word': {
                'id': word.id,
                'kanji': word.kanji,
                'romaji': word.romaji,
                'english': word.english,
                'parts': word.parts,
                'correct_count': word.correct_count,
                'wrong_count': word.wrong_count
            }
        })
    
    return QuizResult(
        correct_count=correct_count,
        total_questions=len(questions),
        review_items=formatted_review_items
    )

@api_router.get("/sentences", response_model=List[Sentence])
def get_sentences(
    db: Session = Depends(get_db)
):
    # Get user's current level
    progress = db.query(UserProgress).first()
    if not progress:
        progress = UserProgress(current_level='N5')
        db.add(progress)
        db.commit()
    
    # Load sentences from JSON file
    import json
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sentence-constructor.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter sentences by user's level
    user_level = progress.current_level
    filtered_sentences = [
        sentence for sentence in data['sentences']
        if sentence['jlpt_level'] == user_level
    ]
    
    return filtered_sentences

@api_router.post("/sentences/attempt", response_model=SentenceProgress)
def submit_sentence_attempt(
    attempt: SentenceAttempt,
    db: Session = Depends(get_db)
):
    # Get the sentence from the JSON file
    import json
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sentence-constructor.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find the sentence
    sentence = next((s for s in data['sentences'] if s['id'] == attempt.sentence_id), None)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    # Check if the attempt is correct
    correct_sentence = sentence['target_language']['text']
    is_correct = attempt.constructed_sentence.strip() == correct_sentence.strip()
    
    # Update or create progress record
    progress = db.query(SentenceProgressModel).filter_by(sentence_id=attempt.sentence_id).first()
    if not progress:
        progress = SentenceProgressModel(
            sentence_id=attempt.sentence_id,
            attempts=0,
            correct_attempts=0,
            last_attempted=datetime.now(),
            success_rate=0.0
        )
        db.add(progress)
    
    # Update progress
    progress.attempts += 1
    if is_correct:
        progress.correct_attempts += 1
    progress.last_attempted = datetime.now()
    progress.success_rate = progress.correct_attempts / progress.attempts
    
    db.commit()
    db.refresh(progress)
    return progress

# Include the API router
app.include_router(api_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)