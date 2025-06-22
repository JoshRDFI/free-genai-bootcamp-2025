import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the API service
from renpy.game.python.api import APIService, make_web_request

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
        mock_response.json.return_value = {
            "message": {
                "content": "Hello"
            }
        }
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
            "message": {
                "content": json.dumps({
                    "conversation": [
                        {"speaker": "Character1", "japanese": "こんにちは", "english": "Hello"}
                    ]
                })
            }
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.generate_conversation('At a cafe', ['Character1', 'Character2'])
        
        # Assertions
        self.assertEqual(result, [
            {"speaker": "Character1", "japanese": "こんにちは", "english": "Hello"}
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
            "message": {
                "content": json.dumps({
                    "lesson": {
                        "metadata": {"title": "Basic Greetings"},
                        "vocabulary": [{"japanese": "こんにちは", "reading": "こんにちは", "english": "Hello"}],
                        "dialogue_script": [{"speaker": "Sensei", "japanese": "こんにちは", "english": "Hello"}]
                    }
                })
            }
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = APIService.generate_lesson('Basic Greetings')
        
        # Assertions
        self.assertEqual(result, {
            "metadata": {"title": "Basic Greetings"},
            "vocabulary": [{"japanese": "こんにちは", "reading": "こんにちは", "english": "Hello"}],
            "dialogue_script": [{"speaker": "Sensei", "japanese": "こんにちは", "english": "Hello"}]
        })
        mock_post.assert_called_once()

class TestWebRequest(unittest.TestCase):
    """Test cases for the make_web_request function"""
    
    @patch('renpy.game.python.api.is_web_browser')
    @patch('builtins.__import__')
    def test_make_web_request_with_data(self, mock_import, mock_is_web_browser):
        """Test make_web_request when data is provided"""
        # Setup mocks
        mock_is_web_browser.return_value = True
        mock_renpy = MagicMock()
        mock_renpy.fetch.return_value = MagicMock(
            status_code=200,
            text='{"result": "success"}'
        )
        mock_import.return_value = mock_renpy
        
        # Test data
        data = {"test": "data"}
        
        # Call the function
        response = make_web_request('POST', 'http://test.com', data=data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '{"result": "success"}')
        mock_renpy.fetch.assert_called_once()
        
        # Verify the call was made with proper parameters
        call_args = mock_renpy.fetch.call_args
        self.assertEqual(call_args[0][0], 'http://test.com')  # URL
        self.assertEqual(call_args[1]['method'], 'POST')
        self.assertEqual(call_args[1]['data'], json.dumps(data))
    
    @patch('renpy.game.python.api.is_web_browser')
    @patch('builtins.__import__')
    def test_make_web_request_without_data(self, mock_import, mock_is_web_browser):
        """Test make_web_request when no data is provided (this tests our fix)"""
        # Setup mocks
        mock_is_web_browser.return_value = True
        mock_renpy = MagicMock()
        mock_renpy.fetch.return_value = MagicMock(
            status_code=200,
            text='{"result": "success"}'
        )
        mock_import.return_value = mock_renpy
        
        # Call the function without data
        response = make_web_request('GET', 'http://test.com')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '{"result": "success"}')
        mock_renpy.fetch.assert_called_once()
        
        # Verify the call was made with empty string for data (our fix)
        call_args = mock_renpy.fetch.call_args
        self.assertEqual(call_args[0][0], 'http://test.com')  # URL
        self.assertEqual(call_args[1]['method'], 'GET')
        self.assertEqual(call_args[1]['data'], "")  # Should be empty string, not None
    
    @patch('renpy.game.python.api.is_web_browser')
    @patch('builtins.__import__')
    def test_make_web_request_fetchfile_fallback_with_data(self, mock_import, mock_is_web_browser):
        """Test make_web_request fallback to fetchFile when data is provided"""
        # Setup mocks
        mock_is_web_browser.return_value = True
        
        # Mock renpy without fetch attribute to trigger fallback
        mock_renpy = MagicMock()
        delattr(mock_renpy, 'fetch')
        
        # Mock emscripten
        mock_emscripten = MagicMock()
        mock_emscripten.run_script.side_effect = [
            '"function"',  # fetchFile availability check
            '123',  # fetchFile ID
            'OK 200 Success'  # fetchFileResult
        ]
        
        # Configure import to return appropriate mocks
        def import_side_effect(name, *args, **kwargs):
            if name == 'renpy':
                return mock_renpy
            elif name == 'emscripten':
                return mock_emscripten
            else:
                return MagicMock()
        
        mock_import.side_effect = import_side_effect
        
        # Test data
        data = {"test": "data"}
        
        # Call the function
        response = make_web_request('POST', 'http://test.com', data=data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'Success')
        
        # Verify fetchFile was called with proper parameters
        fetchfile_call = mock_emscripten.run_script.call_args_list[1]
        self.assertIn('fetchFile("POST"', fetchfile_call[0][0])
        self.assertIn('"http://test.com"', fetchfile_call[0][0])
        # Should not contain "None" for data_file parameter
        self.assertNotIn('None', fetchfile_call[0][0])
    
    @patch('renpy.game.python.api.is_web_browser')
    @patch('builtins.__import__')
    def test_make_web_request_fetchfile_fallback_without_data(self, mock_import, mock_is_web_browser):
        """Test make_web_request fallback to fetchFile when no data is provided (tests our fix)"""
        # Setup mocks
        mock_is_web_browser.return_value = True
        
        # Mock renpy without fetch attribute to trigger fallback
        mock_renpy = MagicMock()
        delattr(mock_renpy, 'fetch')
        
        # Mock emscripten
        mock_emscripten = MagicMock()
        mock_emscripten.run_script.side_effect = [
            '"function"',  # fetchFile availability check
            '123',  # fetchFile ID
            'OK 200 Success'  # fetchFileResult
        ]
        
        # Configure import to return appropriate mocks
        def import_side_effect(name, *args, **kwargs):
            if name == 'renpy':
                return mock_renpy
            elif name == 'emscripten':
                return mock_emscripten
            else:
                return MagicMock()
        
        mock_import.side_effect = import_side_effect
        
        # Call the function without data
        response = make_web_request('GET', 'http://test.com')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'Success')
        
        # Verify fetchFile was called with empty string for data_file (our fix)
        fetchfile_call = mock_emscripten.run_script.call_args_list[1]
        self.assertIn('fetchFile("GET"', fetchfile_call[0][0])
        self.assertIn('"http://test.com"', fetchfile_call[0][0])
        # Should contain empty string for data_file parameter, not None
        self.assertIn('""', fetchfile_call[0][0])
        self.assertNotIn('None', fetchfile_call[0][0])

if __name__ == '__main__':
    unittest.main()