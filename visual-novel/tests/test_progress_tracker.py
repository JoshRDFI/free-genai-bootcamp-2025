import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the progress tracker
from renpy.game.python.progress import ProgressTracker

class TestProgressTracker(unittest.TestCase):
    """Test cases for the Progress Tracker"""
    
    def setUp(self):
        self.tracker = ProgressTracker(1)
    
    @patch('renpy.game.python.progress.APIService.save_progress')
    def test_save_progress(self, mock_save_progress):
        # Setup mock response
        mock_save_progress.return_value = {'status': 'success'}
        
        # Call the method
        result = self.tracker.save_progress('lesson1', 'intro', True)
        
        # Assertions
        self.assertEqual(result, {'status': 'success'})
        self.assertEqual(self.tracker.current_lesson, 'lesson1')
        self.assertEqual(self.tracker.current_scene, 'intro')
        self.assertIn('lesson1:intro', self.tracker.completed_scenes)
        mock_save_progress.assert_called_once_with(1, 'lesson1', 'intro', True)
    
    def test_is_scene_completed(self):
        # Add a completed scene
        self.tracker.completed_scenes.add('lesson1:intro')
        
        # Test a completed scene
        self.assertTrue(self.tracker.is_scene_completed('lesson1', 'intro'))
        
        # Test an incomplete scene
        self.assertFalse(self.tracker.is_scene_completed('lesson1', 'practice'))
    
    @patch('renpy.game.python.progress.APIService.add_vocabulary')
    def test_add_vocabulary(self, mock_add_vocabulary):
        # Setup mock response
        mock_add_vocabulary.return_value = {
            'id': 1,
            'japanese': 'u3053u3093u306bu3061u306f',
            'reading': 'u3053u3093u306bu3061u306f',
            'english': 'Hello'
        }
        
        # Call the method
        result = self.tracker.add_vocabulary('u3053u3093u306bu3061u306f', 'u3053u3093u306bu3061u306f', 'Hello')
        
        # Assertions
        self.assertEqual(result, {
            'id': 1,
            'japanese': 'u3053u3093u306bu3061u306f',
            'reading': 'u3053u3093u306bu3061u306f',
            'english': 'Hello'
        })
        self.assertEqual(len(self.tracker.vocabulary), 1)
        self.assertEqual(self.tracker.vocabulary[0]['japanese'], 'u3053u3093u306bu3061u306f')
        mock_add_vocabulary.assert_called_once_with(
            1, 'u3053u3093u306bu3061u306f', 'u3053u3093u306bu3061u306f', 'Hello', 'lesson1'
        )
    
    @patch('renpy.game.python.progress.APIService.add_vocabulary')
    def test_add_vocabulary_error(self, mock_add_vocabulary):
        # Setup mock to return an error
        mock_add_vocabulary.return_value = {'error': 'Database error'}
        
        # Call the method
        result = self.tracker.add_vocabulary('u3053u3093u306bu3061u306f')
        
        # Assertions
        self.assertEqual(result, {'error': 'Database error'})
        self.assertEqual(len(self.tracker.vocabulary), 0)  # No vocabulary should be added locally
    
    def test_update_mastery(self):
        # Call the method
        self.tracker.update_mastery('word1', 3)
        
        # Assertions
        self.assertEqual(self.tracker.mastery_levels['word1'], 3)

if __name__ == '__main__':
    unittest.main()