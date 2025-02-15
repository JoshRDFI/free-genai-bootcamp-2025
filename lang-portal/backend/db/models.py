# backend/db/models.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for many-to-many relationship between words and groups
word_groups = Table(
    'word_groups', Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

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

    def to_dict(self):
        return {
            'id': self.id,
            'kanji': self.kanji,
            'romaji': self.romaji,
            'english': self.english,
            'parts': self.parts,
            'correct_count': self.correct_count,
            'wrong_count': self.wrong_count,
            'groups': [group.to_dict() for group in self.groups]
        }

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    words_count = Column(Integer, default=0)
    words = relationship('Word', secondary=word_groups, back_populates='groups')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'words_count': self.words_count,
            'words': [word.to_dict() for word in self.words]
        }

class StudyActivity(Base):
    __tablename__ = 'study_activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

class StudySession(Base):
    __tablename__ = 'study_sessions'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    study_activity_id = Column(Integer, ForeignKey('study_activities.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
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
            'group': self.group.to_dict(),
            'study_activity': self.study_activity.to_dict(),
            'review_items': [review.to_dict() for review in self.review_items]
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
            'word': self.word.to_dict(),
            'session': self.session.to_dict()
        }

# Add back_populates to the Group and StudyActivity models
Group.sessions = relationship('StudySession', back_populates='group')
StudyActivity.sessions = relationship('StudySession', back_populates='study_activity')

# Add back_populates to the Word model
Word.review_items = relationship('WordReviewItem', back_populates='word')