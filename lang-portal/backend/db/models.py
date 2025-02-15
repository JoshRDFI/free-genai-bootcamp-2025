from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
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

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    words = relationship('Word', secondary=word_groups, back_populates='groups')

class StudyActivity(Base):
    __tablename__ = 'study_activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

class StudySession(Base):
    __tablename__ = 'study_sessions'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    study_activity_id = Column(Integer, ForeignKey('study_activities.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    group = relationship('Group', back_populates='sessions')
    study_activity = relationship('StudyActivity', back_populates='sessions')
    review_items = relationship('WordReviewItem', back_populates='session')

class WordReviewItem(Base):
    __tablename__ = 'word_review_items'
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'))
    study_session_id = Column(Integer, ForeignKey('study_sessions.id'))
    correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())
    word = relationship('Word', back_populates='review_items')
    session = relationship('StudySession', back_populates='review_items')

# Add back_populates to the Group and StudyActivity models
Group.sessions = relationship('StudySession', back_populates='group')
StudyActivity.sessions = relationship('StudySession', back_populates='study_activity')

# Add back_populates to the Word model
Word.review_items = relationship('WordReviewItem', back_populates='word')