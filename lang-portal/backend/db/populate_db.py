# populate_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Word, WordGroup

# Create the database engine
engine = create_engine("sqlite:///./langportal.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a session
db = SessionLocal()

# Create word groups
group1 = WordGroup(name="Basic Japanese")
group2 = WordGroup(name="Intermediate Japanese")

# Add word groups to the session
db.add(group1)
db.add(group2)
db.commit()

# Create words and associate them with word groups
word1 = Word(kanji="こんにちは", romaji="konnichiwa", english="hello", group_id=group1.id)
word2 = Word(kanji="ありがとう", romaji="arigatou", english="thank you", group_id=group1.id)
word3 = Word(kanji="さようなら", romaji="sayounara", english="goodbye", group_id=group1.id)
word4 = Word(kanji="元気", romaji="genki", english="well", group_id=group2.id)
word5 = Word(kanji="疲れる", romaji="tsukareru", english="to be tired", group_id=group2.id)

# Add words to the session
db.add(word1)
db.add(word2)
db.add(word3)
db.add(word4)
db.add(word5)
db.commit()

# Close the session
db.close()