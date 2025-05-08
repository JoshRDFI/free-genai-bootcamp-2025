import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the API service
from renpy.game.python.api import APIService

class TestAPIService(unittest.TestCase):
    """Test cases for the API Service"""
    
    @patch('renpy.game.python.api.requests.post')
    def test_save_progress(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'success'}
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.save_progress(1, 'lesson1', 'intro', True)
        
        # Assertions
        self.assertEqual(result, {'status': 'success'})
        mock_post.assert_called_once()
        
    @patch('renpy.game.python.api.requests.post')
    def test_save_progress_error(self, mock_post):
        # Setup mock to raise an exception
        mock_post.side_effect = Exception('Connection error')
        
        # Call the method
        result = APIService.save_progress(1, 'lesson1', 'intro', True)
        
        # Assertions
        self.assertEqual(result, {'error': 'Connection error'})
    
    @patch('renpy.game.python.api.requests.post')
    def test_get_translation(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'text': 'Hello'}
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.get_translation('こんにちは')
        
        # Assertions
        self.assertEqual(result, 'Hello')
        mock_post.assert_called_once()
    
    @patch('renpy.game.python.api.requests.post')
    def test_get_translation_error(self, mock_post):
        # Setup mock to raise an exception
        mock_post.side_effect = Exception('Connection error')
        
        # Call the method
        result = APIService.get_translation('こんにちは')
        
        # Assertions
        self.assertEqual(result, 'Translation failed')
    
    @patch('renpy.game.python.api.requests.post')
    def test_get_audio(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'audio_path': '/path/to/audio.mp3'}
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.get_audio('こんにちは')
        
        # Assertions
        self.assertEqual(result, '/path/to/audio.mp3')
        mock_post.assert_called_once()
    
    @patch('renpy.game.python.api.requests.post')
    def test_get_audio_error(self, mock_post):
        # Setup mock to raise an exception
        mock_post.side_effect = Exception('Connection error')
        
        # Call the method
        result = APIService.get_audio('こんにちは')
        
        # Assertions
        self.assertIsNone(result)
    
    @patch('renpy.game.python.api.requests.post')
    def test_add_vocabulary(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 1, 'japanese': 'こんにちは'}
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.add_vocabulary(1, 'こんにちは', 'こんにちは', 'Hello')
        
        # Assertions
        self.assertEqual(result, {'id': 1, 'japanese': 'こんにちは'})
        mock_post.assert_called_once()
    
    @patch('renpy.game.python.api.requests.post')
    def test_generate_conversation(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'conversation': [
                {'speaker': 'Character1', 'japanese_text': 'こんにちは', 'english_translation': 'Hello'}
            ]
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.generate_conversation('At a cafe', ['Character1', 'Character2'])
        
        # Assertions
        self.assertEqual(result, [
            {'speaker': 'Character1', 'japanese_text': 'こんにちは', 'english_translation': 'Hello'}
        ])
        mock_post.assert_called_once()
    
    @patch('renpy.game.python.api.requests.post')
    def test_generate_conversation_error(self, mock_post):
        # Setup mock to return an error status code
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.generate_conversation('At a cafe', ['Character1', 'Character2'])
        
        # Assertions
        self.assertIsNone(result)
    
    @patch('renpy.game.python.api.requests.post')
    def test_generate_lesson(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'lesson': {
                'metadata': {'title': 'Basic Greetings'},
                'vocabulary': [{'japanese': 'こんにちは', 'reading': 'こんにちは', 'english': 'Hello'}],
                'dialogue_script': [{'speaker': 'Sensei', 'japanese': 'こんにちは', 'english': 'Hello'}]
            }
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.generate_lesson('Basic Greetings')
        
        # Assertions
        self.assertEqual(result, {
            'metadata': {'title': 'Basic Greetings'},
            'vocabulary': [{'japanese': 'こんにちは', 'reading': 'こんにちは', 'english': 'Hello'}],
            'dialogue_script': [{'speaker': 'Sensei', 'japanese': 'こんにちは', 'english': 'Hello'}]
        })
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()