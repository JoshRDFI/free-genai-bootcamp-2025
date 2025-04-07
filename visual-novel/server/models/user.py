# User model

class User:
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