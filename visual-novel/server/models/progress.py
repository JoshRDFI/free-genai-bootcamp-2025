from app import db

class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.String(255), nullable=False)
    scene_id = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'scene_id': self.scene_id,
            'completed': self.completed,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

    """Progress model for tracking user learning progress"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.lessons_completed = []
        self.vocabulary_mastered = []
        self.grammar_points_learned = []
        self.total_study_time = 0  # in minutes
        
    def to_dict(self):
        """Convert progress object to dictionary"""
        return {
            'user_id': self.user_id,
            'lessons_completed': self.lessons_completed,
            'vocabulary_mastered': self.vocabulary_mastered,
            'grammar_points_learned': self.grammar_points_learned,
            'total_study_time': self.total_study_time
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create progress object from dictionary"""
        progress = cls(data['user_id'])
        progress.lessons_completed = data.get('lessons_completed', [])
        progress.vocabulary_mastered = data.get('vocabulary_mastered', [])
        progress.grammar_points_learned = data.get('grammar_points_learned', [])
        progress.total_study_time = data.get('total_study_time', 0)
        return progress