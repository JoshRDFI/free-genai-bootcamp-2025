# Progress tracking for the visual novel

from .api import APIService

class ProgressTracker:
    """Tracks player progress through the visual novel"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_lesson = "lesson1"
        self.current_scene = "intro"
        self.completed_scenes = set()
        self.vocabulary = []
        self.mastery_levels = {}
    
    def save_progress(self, lesson_id=None, scene_id=None, completed=False):
        """Save current progress to the server"""
        if lesson_id is None:
            lesson_id = self.current_lesson
        if scene_id is None:
            scene_id = self.current_scene
            
        # Update local state
        self.current_lesson = lesson_id
        self.current_scene = scene_id
        if completed:
            self.completed_scenes.add(f"{lesson_id}:{scene_id}")
        
        # Save to server via API
        return APIService.save_progress(self.user_id, lesson_id, scene_id, completed)
    
    def is_scene_completed(self, lesson_id, scene_id):
        """Check if a scene has been completed"""
        return f"{lesson_id}:{scene_id}" in self.completed_scenes
    
    def add_vocabulary(self, japanese, reading=None, english=None):
        """Add vocabulary to player's list"""
        # Save to server via API
        result = APIService.add_vocabulary(
            self.user_id, japanese, reading, english, self.current_lesson
        )
        
        # Update local state if successful
        if result and "error" not in result:
            self.vocabulary.append({
                "japanese": japanese,
                "reading": reading,
                "english": english,
                "lesson_id": self.current_lesson
            })
        
        return result
    
    def update_mastery(self, word_id, level):
        """Update mastery level for a vocabulary word"""
        self.mastery_levels[word_id] = level
        # This would typically also update the server
        # Implementation depends on the API structure