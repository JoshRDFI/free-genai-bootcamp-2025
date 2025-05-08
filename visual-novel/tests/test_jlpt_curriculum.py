import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the JLPT curriculum
from renpy.game.python.jlpt import JLPTCurriculum

class TestJLPTCurriculum(unittest.TestCase):
    """Test cases for the JLPT Curriculum"""
    
    def setUp(self):
        self.curriculum = JLPTCurriculum()
    
    def test_get_lesson(self):
        # Test getting an existing lesson
        lesson = self.curriculum.get_lesson('lesson1')
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson['title'], 'Basic Greetings')
        
        # Test getting a non-existent lesson
        lesson = self.curriculum.get_lesson('nonexistent')
        self.assertIsNone(lesson)
    
    def test_get_grammar_points(self):
        # Test getting all grammar points
        all_points = self.curriculum.get_grammar_points()
        self.assertGreater(len(all_points), 0)
        
        # Test getting grammar points by category
        basic_points = self.curriculum.get_grammar_points('basic')
        self.assertGreater(len(basic_points), 0)
        self.assertIn('Basic sentence structure (Subject + Object + Verb)', basic_points)
        
        # Test getting grammar points for a non-existent category
        nonexistent_points = self.curriculum.get_grammar_points('nonexistent')
        self.assertEqual(len(nonexistent_points), 0)
    
    def test_get_vocabulary_categories(self):
        # Test getting all vocabulary categories
        categories = self.curriculum.get_vocabulary_categories()
        self.assertGreater(len(categories), 0)
        self.assertIn('Greetings', categories)

if __name__ == '__main__':
    unittest.main()