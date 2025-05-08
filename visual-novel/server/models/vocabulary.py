from app import db

class Vocabulary(db.Model):
    __tablename__ = 'vocabulary'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    japanese = db.Column(db.String(255), nullable=False)
    reading = db.Column(db.String(255))
    english = db.Column(db.String(255))
    lesson_id = db.Column(db.String(255))
    mastery_level = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'japanese': self.japanese,
            'reading': self.reading,
            'english': self.english,
            'lesson_id': self.lesson_id,
            'mastery_level': self.mastery_level,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None
        }

    """Model for vocabulary items in the JLPT N5 curriculum"""
    
    def __init__(self, word_id, japanese, reading, english, lesson_id):
        self.word_id = word_id
        self.japanese = japanese  # Kanji/kana form
        self.reading = reading    # Hiragana reading
        self.english = english    # English translation
        self.lesson_id = lesson_id
        self.part_of_speech = None
        self.example_sentences = []
        
    def to_dict(self):
        """Convert vocabulary item to dictionary"""
        return {
            'word_id': self.word_id,
            'japanese': self.japanese,
            'reading': self.reading,
            'english': self.english,
            'lesson_id': self.lesson_id,
            'part_of_speech': self.part_of_speech,
            'example_sentences': self.example_sentences
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create vocabulary item from dictionary"""
        item = cls(
            data['word_id'],
            data['japanese'],
            data['reading'],
            data['english'],
            data['lesson_id']
        )
        item.part_of_speech = data.get('part_of_speech')
        item.example_sentences = data.get('example_sentences', [])
        return item