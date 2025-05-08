# User model

from app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=db.func.now())
    last_login = db.Column(db.DateTime)

    # Relationships
    progress_items = db.relationship('Progress', backref='user', lazy=True)
    vocabulary_items = db.relationship('Vocabulary', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    """User model for the visual novel application"""
    
    def __init__(self, user_id, username, email=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = None
        self.last_login = None
        
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create user object from dictionary"""
        user = cls(data['user_id'], data['username'], data.get('email'))
        user.created_at = data.get('created_at')
        user.last_login = data.get('last_login')
        return user