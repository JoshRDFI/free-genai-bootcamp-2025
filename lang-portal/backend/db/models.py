# backend/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Table, create_engine, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between words and groups
word_groups = Table(
    'word_groups', Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

class UserProgress(Base):
    __tablename__ = 'user_progress'
    id = Column(Integer, primary_key=True)
    current_level = Column(String, nullable=False, default='N5')  # N5, N4, N3, N2, N1
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'current_level': self.current_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    kanji = Column(String, nullable=False)
    romaji = Column(String, nullable=False)
    english = Column(String, nullable=False)
    parts = Column(JSON, nullable=False)  # Will store: {level: str, strokes: int, strokeOrder: List[Dict[str, List[float]]]}
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    groups = relationship('Group', secondary=word_groups, back_populates='words')
    review_items = relationship('WordReviewItem', back_populates='word')

    def to_dict(self):
        return {
            'id': self.id,
            'kanji': self.kanji,
            'romaji': self.romaji,
            'english': self.english,
            'parts': self.parts,
            'correct_count': self.correct_count,
            'wrong_count': self.wrong_count,
            'group_ids': [group.id for group in self.groups]
        }

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    words_count = Column(Integer, default=0)
    words = relationship('Word', secondary=word_groups, back_populates='groups')
    sessions = relationship('StudySession', back_populates='group')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'words_count': self.words_count,
            'word_ids': [word.id for word in self.words]
        }

class StudyActivity(Base):
    __tablename__ = 'study_activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    thumbnail = Column(String, nullable=False)  # URL to the thumbnail image
    url = Column(String, nullable=False)  # URL to launch the activity
    sessions = relationship('StudySession', back_populates='study_activity')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'thumbnail': self.thumbnail,
            'url': self.url
        }

class StudySession(Base):
    __tablename__ = 'study_sessions'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    study_activity_id = Column(Integer, ForeignKey('study_activities.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    quiz_metadata = Column(JSON, default=dict)
    group = relationship('Group', back_populates='sessions')
    study_activity = relationship('StudyActivity', back_populates='sessions')
    review_items = relationship('WordReviewItem', back_populates='session')

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'study_activity_id': self.study_activity_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'quiz_metadata': self.quiz_metadata,
            'review_item_ids': [review.id for review in self.review_items]
        }

class WordReviewItem(Base):
    __tablename__ = 'word_review_items'
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    study_session_id = Column(Integer, ForeignKey('study_sessions.id'), nullable=False)
    correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())
    word = relationship('Word', back_populates='review_items')
    session = relationship('StudySession', back_populates='review_items')

    def to_dict(self):
        return {
            'id': self.id,
            'word_id': self.word_id,
            'study_session_id': self.study_session_id,
            'correct': self.correct,
            'created_at': self.created_at.isoformat(),
            'word': self.word.to_dict() if self.word else None
        }

class SentenceProgress(Base):
    __tablename__ = "sentence_progress"

    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(String, index=True)
    attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    last_attempted = Column(DateTime, default=datetime.now)
    success_rate = Column(Float, default=0.0)

class ListeningQuestion(Base):
    __tablename__ = 'listening_questions'
    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey('listening_exercises.id'), nullable=False)
    question_type = Column(String, nullable=False)  # multiple_choice, fill_blank, true_false
    question_text = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # List of possible answers
    points = Column(Integer, default=1)
    exercise = relationship('ListeningExercise', back_populates='questions')

    def to_dict(self):
        return {
            'id': self.id,
            'exercise_id': self.exercise_id,
            'question_type': self.question_type,
            'question_text': self.question_text,
            'correct_answer': self.correct_answer,
            'options': self.options,
            'points': self.points
        }

class ListeningExercise(Base):
    __tablename__ = 'listening_exercises'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    audio_file = Column(String, nullable=False)  # Path to the audio file
    difficulty = Column(String, nullable=False)  # Beginner, Intermediate, Advanced
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    questions = relationship('ListeningQuestion', back_populates='exercise', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'audio_file': self.audio_file,
            'difficulty': self.difficulty,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'questions': [question.to_dict() for question in self.questions]
        }