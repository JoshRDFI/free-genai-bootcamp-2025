# Database service

import sqlite3
import json
import os
import requests

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self, db_path="/data/shared_db/visual_novel.db", api_base_url=None):
        # Local database path
        self.db_path = db_path
        
        # API endpoint for remote database operations
        self.api_base_url = api_base_url or os.environ.get('OPEA_API_BASE_URL', 'http://opea-api-gateway:8000')
        self.db_api_url = f"{self.api_base_url}/database"
        
        # Determine if we should use local or remote database
        self.use_remote_db = os.environ.get('USE_REMOTE_DB', 'false').lower() == 'true'
        
        if not self.use_remote_db:
            self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Ensure database file and tables exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # Create progress table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            user_id TEXT PRIMARY KEY,
            lessons_completed TEXT,
            vocabulary_mastered TEXT,
            grammar_points_learned TEXT,
            total_study_time INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create vocabulary table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            word_id TEXT PRIMARY KEY,
            japanese TEXT NOT NULL,
            reading TEXT NOT NULL,
            english TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            part_of_speech TEXT,
            example_sentences TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def get_user(self, user_id):
        """Get user by ID"""
        if self.use_remote_db:
            try:
                response = requests.get(f"{self.db_api_url}/users/{user_id}")
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error calling database API: {e}")
                return None
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            conn.close()
            
            if user_data:
                return {
                    'user_id': user_data[0],
                    'username': user_data[1],
                    'email': user_data[2],
                    'created_at': user_data[3],
                    'last_login': user_data[4]
                }
            return None
    
    def save_user(self, user_data):
        """Save user to database"""
        if self.use_remote_db:
            try:
                response = requests.post(
                    f"{self.db_api_url}/users",
                    json=user_data
                )
                return response.status_code == 200 or response.status_code == 201
            except Exception as e:
                print(f"Error calling database API: {e}")
                return False
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, username, email) VALUES (?, ?, ?)",
                (user_data['user_id'], user_data['username'], user_data.get('email'))
            )
            
            conn.commit()
            conn.close()
            return True
    
    def get_progress(self, user_id):
        """Get progress for user"""
        if self.use_remote_db:
            try:
                response = requests.get(f"{self.db_api_url}/progress/{user_id}")
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error calling database API: {e}")
                return None
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
            progress_data = cursor.fetchone()
            
            conn.close()
            
            if progress_data:
                return {
                    'user_id': progress_data[0],
                    'lessons_completed': json.loads(progress_data[1]) if progress_data[1] else [],
                    'vocabulary_mastered': json.loads(progress_data[2]) if progress_data[2] else [],
                    'grammar_points_learned': json.loads(progress_data[3]) if progress_data[3] else [],
                    'total_study_time': progress_data[4]
                }
            return None
    
    def save_progress(self, progress_data):
        """Save progress to database"""
        if self.use_remote_db:
            try:
                response = requests.post(
                    f"{self.db_api_url}/progress",
                    json=progress_data
                )
                return response.status_code == 200 or response.status_code == 201
            except Exception as e:
                print(f"Error calling database API: {e}")
                return False
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT OR REPLACE INTO progress 
                (user_id, lessons_completed, vocabulary_mastered, grammar_points_learned, total_study_time) 
                VALUES (?, ?, ?, ?, ?)""",
                (
                    progress_data['user_id'],
                    json.dumps(progress_data.get('lessons_completed', [])),
                    json.dumps(progress_data.get('vocabulary_mastered', [])),
                    json.dumps(progress_data.get('grammar_points_learned', [])),
                    progress_data.get('total_study_time', 0)
                )
            )
            
            conn.commit()
            conn.close()
            return True