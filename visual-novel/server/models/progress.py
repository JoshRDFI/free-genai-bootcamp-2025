# Progress model

class Progress:
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