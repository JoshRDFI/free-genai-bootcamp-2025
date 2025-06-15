# backend/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Table, create_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

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
    parts = Column(JSON, nullable=False)
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