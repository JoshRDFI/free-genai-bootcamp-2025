# JLPT N5 curriculum logic

class JLPTCurriculum:
    """Handles JLPT curriculum content and progression"""
    
    def __init__(self):
        # JLPT N5 grammar points by category
        self.grammar_points = {
            "basic": [
                "Basic sentence structure (Subject + Object + Verb)",
                "Desu/masu form",
                "Basic particles (は, が, を, に, で)",
                "Question markers with か",
                "Demonstratives (これ, それ, あれ)"
            ],
            "intermediate": [
                "Te-form for requests",
                "Past tense",
                "Negative form",
                "Adjective conjugation",
                "Basic counters"
            ],
            "advanced": [
                "~たい for expressing desire",
                "~ている for ongoing actions",
                "~ことができる for ability",
                "~から for reasons",
                "~ましょう for suggestions"
            ]
        }
        
        # JLPT N5 vocabulary categories
        self.vocabulary_categories = [
            "Greetings",
            "Self-introduction",
            "Family",
            "Numbers and time",
            "Daily activities",
            "Food and drink",
            "Transportation",
            "Shopping",
            "Weather",
            "Locations"
        ]
        
        # Lesson structure
        self.lessons = [
            {
                "id": "lesson1",
                "title": "Basic Greetings",
                "grammar": ["Desu/masu form", "Basic particles (は, が)"],
                "vocabulary": ["Greetings", "Self-introduction"],
                "scenes": ["intro", "greeting", "self_intro", "practice", "review"]
            },
            {
                "id": "lesson2",
                "title": "At the Cafe",
                "grammar": ["Basic sentence structure", "Question markers with か", "Particle を for direct objects"],
                "vocabulary": ["Food and drink items", "Basic verbs"],
                "scenes": ["intro", "ordering", "price", "thanking", "review"]
            },
            {
                "id": "lesson3",
                "title": "Shopping",
                "grammar": ["Adjectives", "Particle が for existence", "Numbers and counting"],
                "vocabulary": ["Clothing items", "Colors", "Numbers 1-10"],
                "scenes": ["intro", "describing", "asking", "buying", "review"]
            }
            # Add more lessons as needed
        ]
    
    def get_lesson(self, lesson_id):
        """Get lesson data by ID"""
        for lesson in self.lessons:
            if lesson["id"] == lesson_id:
                return lesson
        return None
    
    def get_grammar_points(self, category=None):
        """Get grammar points, optionally filtered by category"""
        if category and category in self.grammar_points:
            return self.grammar_points[category]
        elif not category:
            # Return all grammar points flattened
            all_points = []
            for points in self.grammar_points.values():
                all_points.extend(points)
            return all_points
        return []
    
    def get_vocabulary_categories(self):
        """Get all vocabulary categories"""
        return self.vocabulary_categories