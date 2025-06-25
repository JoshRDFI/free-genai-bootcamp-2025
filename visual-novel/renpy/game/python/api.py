# API communication module for Japanese Learning Visual Novel
# This module provides access to services through the Flask API gateway

import requests
import json
import os
import base64
from io import BytesIO
import tempfile
import time
import sys
import datetime
import renpy.exports as renpy

# Global variable for emscripten module (will be set if available)
emscripten = None

# Debug flag - set to False to disable verbose logging
DEBUG_MODE = True

def debug_print(message):
    """Write debug messages to a log file instead of printing to screen"""
    try:
        log_dir = os.path.join(renpy.config.gamedir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = os.path.join(log_dir, "api_debug.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass  # Silently fail if logging doesn't work

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    # Hardcode the environment variables since .env file loading is unreliable in web builds
    debug_print("Using hardcoded environment variables for web build")
    
    # Set essential environment variables for web builds
    os.environ['FLASK_SERVER_URL'] = 'http://localhost:8001'
    os.environ['SECRET_KEY'] = 'your-secret-key'
    os.environ['FLASK_DEBUG'] = 'true'
    os.environ['USE_REMOTE_DB'] = 'true'
    
    debug_print("Set hardcoded FLASK_SERVER_URL = http://localhost:8001")
    debug_print("Set hardcoded SECRET_KEY = your-secret-key")
    debug_print("Set hardcoded FLASK_DEBUG = true")
    debug_print("Set hardcoded USE_REMOTE_DB = true")

# Load environment variables
load_env_file()

# Try to import emscripten if available
try:
    import emscripten
    debug_print("Successfully imported emscripten module")
except ImportError:
    debug_print("emscripten module not available")
    emscripten = None

# Cache for web browser detection to avoid timing issues
_web_browser_cache = None

def is_web_browser():
    """Detect if we're running in a web browser environment"""
    # Hardcoded to True since this is a web build that only runs in browsers
    return True

def refresh_web_browser_detection():
    """Force refresh the web browser detection cache"""
    global _web_browser_cache
    _web_browser_cache = None
    return is_web_browser()

def get_base_url():
    """Get the base URL for API requests"""
    # Try to get from environment first
    flask_url = os.environ.get('FLASK_SERVER_URL', '')
    debug_print(f"get_base_url: FLASK_SERVER_URL from env = '{flask_url}'")
    if flask_url:
        return flask_url.rstrip('/')
    
    # If no environment variable is set and we're in a web browser,
    # we need to use the nginx server on port 8001
    if is_web_browser():
        # For web browser, use the nginx server on port 8001
        # The nginx server is serving the Ren'Py app and proxying API calls
        debug_print("get_base_url: Using http://localhost:8001 for web browser")
        return "http://localhost:8001"
    
    # For local development, default to localhost
    debug_print("get_base_url: Using http://localhost:8080 for local development")
    return "http://localhost:8080"

# Initialize API endpoints
FLASK_SERVER_URL = get_base_url()
GAME_API_BASE_URL = f"{FLASK_SERVER_URL}/api" if FLASK_SERVER_URL else "/api"

# Build endpoint URLs
LESSON_GENERATION_ENDPOINT = f"{GAME_API_BASE_URL}/generate-lesson"
TRANSLATION_ENDPOINT = f"{GAME_API_BASE_URL}/translate"
TTS_ENDPOINT = f"{GAME_API_BASE_URL}/tts"
CONVERSATION_ENDPOINT = f"{GAME_API_BASE_URL}/generate-conversation"
IMAGE_GEN_ENDPOINT = f"{GAME_API_BASE_URL}/image/generate"
PROGRESS_ENDPOINT = f"{GAME_API_BASE_URL}/progress"
VOCABULARY_ENDPOINT = f"{GAME_API_BASE_URL}/vocabulary"

# Print debug information about loaded endpoints
debug_print(f"FLASK_SERVER_URL = {FLASK_SERVER_URL}")
debug_print(f"LESSON_GENERATION_ENDPOINT = {LESSON_GENERATION_ENDPOINT}")
debug_print(f"GAME_API_BASE_URL = {GAME_API_BASE_URL}")
debug_print(f"Is web browser: {is_web_browser()}")
debug_print(f"Environment FLASK_SERVER_URL: {os.environ.get('FLASK_SERVER_URL', 'NOT_SET')}")

def reinitialize_endpoints():
    """Reinitialize API endpoints - useful if web browser detection changes after module load"""
    global FLASK_SERVER_URL, GAME_API_BASE_URL, LESSON_GENERATION_ENDPOINT, TRANSLATION_ENDPOINT, TTS_ENDPOINT, CONVERSATION_ENDPOINT, IMAGE_GEN_ENDPOINT, PROGRESS_ENDPOINT, VOCABULARY_ENDPOINT
    
    # Force refresh web browser detection
    refresh_web_browser_detection()
    
    # Reinitialize endpoints
    FLASK_SERVER_URL = get_base_url()
    GAME_API_BASE_URL = f"{FLASK_SERVER_URL}/api" if FLASK_SERVER_URL else "/api"
    
    # Rebuild endpoint URLs
    LESSON_GENERATION_ENDPOINT = f"{GAME_API_BASE_URL}/generate-lesson"
    TRANSLATION_ENDPOINT = f"{GAME_API_BASE_URL}/translate"
    TTS_ENDPOINT = f"{GAME_API_BASE_URL}/tts"
    CONVERSATION_ENDPOINT = f"{GAME_API_BASE_URL}/generate-conversation"
    IMAGE_GEN_ENDPOINT = f"{GAME_API_BASE_URL}/image/generate"
    PROGRESS_ENDPOINT = f"{GAME_API_BASE_URL}/progress"
    VOCABULARY_ENDPOINT = f"{GAME_API_BASE_URL}/vocabulary"
    
    debug_print(f"Reinitialized endpoints - FLASK_SERVER_URL = {FLASK_SERVER_URL}")
    debug_print(f"Reinitialized endpoints - Is web browser: {is_web_browser()}")

def make_web_request(method, url, data=None, headers=None):
    """Make a web request with proper error handling for both desktop and web environments"""
    debug_print(f"make_web_request: {method} {url}")
    debug_print(f"make_web_request: data = {data}")
    
    if is_web_browser():
        debug_print("Web browser detected, using Ren'Py's native fetch function")
        
        try:
            fetch = getattr(renpy, 'fetch', None)
            debug_print(f"Found fetch in renpy.exports: {fetch is not None}")
            if fetch is None:
                debug_print("Fetch function not found in renpy.exports")
                raise Exception("Fetch function not available")
            
            try:
                debug_print(f"Starting fetch {method}...")
                
                # Prepare request parameters
                request_data = {
                    'method': method,
                    'url': url,
                    'result': 'json'  # Automatically decode response as JSON
                }
                
                # Handle headers
                if headers:
                    request_data['headers'] = headers
                
                # Handle data/body for different HTTP methods
                if data:
                    if method == 'GET':
                        # For GET requests, append data as query parameters
                        import urllib.parse
                        query_string = urllib.parse.urlencode(data)
                        if '?' in url:
                            url += '&' + query_string
                        else:
                            url += '?' + query_string
                        request_data['url'] = url
                    elif method in ('POST', 'PUT'):
                        # For POST/PUT requests, use the json parameter for Ren'Py fetch
                        if isinstance(data, dict):
                            # Use the json parameter instead of manually encoding
                            request_data['json'] = data
                            debug_print(f"Using 'json' parameter with data: {data}")
                        else:
                            # For non-dict data, use the data parameter
                            request_data['data'] = str(data).encode('utf-8')
                            debug_print(f"Using 'data' parameter with string data: {data}")
                
                debug_print(f"Using fetch {method}: {url}")
                debug_print(f"Request data: {request_data}")
                
                # Add more detailed debugging around the fetch call
                debug_print(f"About to call fetch with parameters: {request_data}")
                debug_print(f"Fetch function type: {type(fetch)}")
                
                # Try to add a simple timeout mechanism using a different approach
                start_time = time.time()
                
                # Make the fetch call directly without any retry mechanism
                debug_print(f"Calling fetch now...")
                
                # Try a simple approach - just call fetch and see if it works
                try:
                    response = fetch(**request_data)
                    debug_print(f"fetch {method} completed successfully: {response}")
                    debug_print(f"Fetch took {time.time() - start_time:.2f} seconds")
                except Exception as immediate_error:
                    debug_print(f"Immediate fetch error: {immediate_error}")
                    raise immediate_error
                
                # Since we're using result="json", response should already be decoded JSON
                # But we need to handle the case where it might still be a response object
                if hasattr(response, 'status_code'):
                    # It's a response object with status_code
                    response_text = str(response)
                    status_code = response.status_code
                else:
                    # It's the decoded JSON data directly - pass it as-is
                    response_text = response  # Don't convert to string!
                    status_code = 200  # Assume success if we got JSON data
                
                debug_print(f"Response status: {status_code}")
                debug_print(f"Response text: {response_text}")
                
                class ResponseWrapper:
                    def __init__(self, text, status_code=200):
                        self.text = text
                        self.status_code = status_code
                    def json(self):
                        import json
                        # If text is already a dict/list (decoded JSON), return it directly
                        if isinstance(self.text, (dict, list)):
                            return self.text
                        # If it's a string representation of JSON, parse it
                        elif isinstance(self.text, str):
                            return json.loads(self.text)
                        # Otherwise, try to parse it as JSON
                        else:
                            return json.loads(str(self.text))
                
                return ResponseWrapper(response_text, status_code)
                
            except Exception as fetch_error:
                debug_print(f"fetch {method} failed with exception: {fetch_error}")
                debug_print(f"Exception type: {type(fetch_error).__name__}")
                debug_print(f"Exception details: {str(fetch_error)}")
                raise fetch_error
                
        except Exception as e:
            debug_print(f"Error in web request: {str(e)}")
            raise e
    else:
        debug_print("Desktop environment detected, using requests library")
        try:
            import requests
            if method == 'GET':
                response = requests.get(url, params=data, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            debug_print(f"Desktop request completed: {response.status_code}")
            return response
        except Exception as e:
            debug_print(f"Desktop request failed: {str(e)}")
            raise e

class APIService:
    """Centralized API service for all external calls"""
    
    @staticmethod
    def test_ollama_connection():
        """Test if Flask server is reachable"""
        try:
            health_url = f"{GAME_API_BASE_URL}/health"
            debug_print(f"Testing connection to {health_url}")
            
            # Use direct request for all environments
            try:
                response = make_web_request('GET', health_url)
                debug_print(f"Flask server connection test status: {response.status_code}")
                return response.status_code == 200
            except Exception as e:
                debug_print(f"Web request failed: {str(e)}")
                debug_print("Server connection failed - servers are required for game functionality")
                return False
                
        except Exception as e:
            debug_print(f"Flask server connection test failed: {str(e)}")
            debug_print("Server connection failed - servers are required for game functionality")
            return False
    
    @staticmethod
    def create_user(username):
        """Create a new user in the database"""
        try:
            user_url = f"{GAME_API_BASE_URL}/user"
            debug_print(f"Creating user with URL: {user_url}")
            debug_print(f"Username: {username}")
            response = make_web_request('POST', user_url, {"username": username})
            debug_print(f"Response status: {response.status_code}")
            debug_print(f"Response text: {response.text}")
            if response.status_code in [200, 201]:  # 200 for existing user, 201 for new user
                result = response.json()
                user_id = result.get("id")
                debug_print(f"User creation successful: {result}")
                return user_id
            else:
                debug_print(f"Failed to create user: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            debug_print(f"Failed to create user: {str(e)}")
            return None
    
    @staticmethod
    def save_progress(user_id, lesson_id, scene_id, completed=False):
        """Save player progress to the server"""
        try:
            progress_url = PROGRESS_ENDPOINT
            
            response = make_web_request('POST', progress_url, {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "scene_id": scene_id,
                "completed": completed
            })
            return response.json()
        except Exception as e:
            debug_print(f"Failed to save progress: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_translation(text, source_lang="ja", target_lang="en"):
        """Get translation for text using translation service"""
        try:
            translation_url = TRANSLATION_ENDPOINT
            
            response = make_web_request('POST', translation_url, {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            })
            return response.json()
        except Exception as e:
            debug_print(f"Translation failed: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_audio(text, voice="female"):
        """Get audio for text using TTS service"""
        try:
            tts_url = TTS_ENDPOINT
            
            response = make_web_request('POST', tts_url, {
                "text": text,
                "voice_id": voice,
                "language": "ja",
                "speed": 1.0
            })
            
            result = response.json()
            if "audio" in result:
                # The TTS service returns base64 encoded audio
                audio_data = base64.b64decode(result["audio"])
                
                # Save to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                    f.write(audio_data)
                    temp_path = f.name
                
                debug_print(f"Audio saved to temporary file: {temp_path}")
                return temp_path
            else:
                debug_print(f"TTS service error: {result}")
                return None
                
        except Exception as e:
            debug_print(f"TTS failed: {str(e)}")
            return None
    
    @staticmethod
    def speech_to_text(audio_path, language="ja-JP"):
        """Convert speech to text using ASR service"""
        try:
            asr_url = f"{GAME_API_BASE_URL}/speech-to-text"
            
            # Read the audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Encode as base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            response = make_web_request('POST', asr_url, {
                "audio": audio_b64,
                "language": language
            })
            
            return response.json()
        except Exception as e:
            debug_print(f"Speech to text failed: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def add_vocabulary(user_id, japanese, reading=None, english=None, lesson_id=None):
        """Add vocabulary to user's study list"""
        try:
            vocab_url = VOCABULARY_ENDPOINT
            
            response = make_web_request('POST', vocab_url, {
                "user_id": user_id,
                "japanese": japanese,
                "reading": reading,
                "english": english,
                "lesson_id": lesson_id
            })
            
            return response.json()
        except Exception as e:
            debug_print(f"Failed to add vocabulary: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_image(prompt, image_type="background", negative_prompt=None, 
                      width=512, height=512, style="anime"):
        """Generate an image using the image generation service"""
        try:
            image_url = IMAGE_GEN_ENDPOINT
            
            debug_print(f"Starting image generation for prompt: {prompt}")
            
            # Generate image using the image generation service
            response = make_web_request('POST', image_url, {
                "prompt": prompt,
                "image_type": image_type,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "style": style
            })
            
            debug_print(f"Image generation response status: {response.status_code}")
            
            result = response.json()
            if "image" in result:
                # The service returns base64 encoded image
                image_data = base64.b64decode(result["image"])
                
                # Save to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                    f.write(image_data)
                    temp_path = f.name
                
                debug_print(f"Image saved to temporary file: {temp_path}")
                return temp_path
            else:
                debug_print(f"Image generation error: {result}")
                return None
                
        except Exception as e:
            debug_print(f"Image generation failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_conversation(context, characters, grammar_points=None, vocabulary=None, num_exchanges=3):
        """Generate a conversation using the conversation service"""
        try:
            conversation_url = CONVERSATION_ENDPOINT
            
            debug_print(f"Starting conversation generation with {num_exchanges} exchanges")
            
            # Generate conversation using the conversation service
            response = make_web_request('POST', conversation_url, {
                "context": context,
                "characters": characters,
                "grammar_points": grammar_points or [],
                "vocabulary": vocabulary or [],
                "num_exchanges": num_exchanges
            })
            
            debug_print(f"Conversation generation response status: {response.status_code}")
            result = response.json()
            debug_print(f"Conversation generation completed successfully")
            return result
            
        except Exception as e:
            debug_print(f"Conversation generation failed: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_lesson(topic, grammar_points=None, vocabulary_focus=None, lesson_number=1, scene_setting="classroom"):
        """Generate a lesson using the lesson generation service with polling"""
        debug_print(f"=== STARTING LESSON GENERATION ===")
        debug_print(f"Topic: {topic}")
        debug_print(f"Grammar points: {grammar_points}")
        debug_print(f"Vocabulary focus: {vocabulary_focus}")
        debug_print(f"Lesson number: {lesson_number}")
        debug_print(f"Scene setting: {scene_setting}")
        debug_print(f"Lesson URL: {LESSON_GENERATION_ENDPOINT}")
        
        try:
            lesson_url = LESSON_GENERATION_ENDPOINT
            
            debug_print(f"Starting lesson generation for topic: {topic}")
            
            # Start the lesson generation (this should return immediately with a job ID)
            response = make_web_request('POST', lesson_url, {
                "topic": topic,
                "grammar_points": grammar_points or [],
                "vocabulary_focus": vocabulary_focus or [],
                "lesson_number": lesson_number,
                "scene_setting": scene_setting
            })
            
            debug_print(f"Lesson generation start response status: {response.status_code}")
            debug_print(f"Lesson generation start response: {response.text}")
            
            if response.status_code != 200:
                debug_print(f"Failed to start lesson generation: {response.status_code}")
                return {"error": f"Failed to start lesson generation: {response.status_code}"}
            
            result = response.json()
            job_id = result.get('job_id')
            
            if not job_id:
                debug_print(f"No job ID returned from lesson generation start")
                return {"error": "No job ID returned from lesson generation start"}
            
            debug_print(f"Lesson generation job started with ID: {job_id}")
            
            # Poll for completion
            max_poll_attempts = 60  # Poll for up to 5 minutes (60 * 5 seconds)
            poll_interval = 5  # Check every 5 seconds
            
            for attempt in range(max_poll_attempts):
                debug_print(f"Polling attempt {attempt + 1}/{max_poll_attempts} for job {job_id}")
                
                # Check job status
                status_url = f"{GAME_API_BASE_URL}/lesson-status/{job_id}"
                status_response = make_web_request('GET', status_url)
                
                if status_response.status_code != 200:
                    debug_print(f"Failed to check job status: {status_response.status_code}")
                    continue
                
                status_result = status_response.json()
                job_status = status_result.get('status')
                
                debug_print(f"Job {job_id} status: {job_status}")
                
                if job_status == 'completed':
                    lesson_data = status_result.get('result')
                    debug_print(f"Lesson generation completed successfully: {lesson_data}")
                    debug_print(f"=== LESSON GENERATION COMPLETE ===")
                    return {'lesson': lesson_data}
                
                elif job_status == 'error':
                    error_msg = status_result.get('error', 'Unknown error')
                    debug_print(f"Lesson generation failed: {error_msg}")
                    debug_print(f"=== LESSON GENERATION FAILED ===")
                    return {"error": f"Lesson generation failed: {error_msg}"}
                
                elif job_status == 'processing':
                    debug_print(f"Lesson generation still processing... (attempt {attempt + 1})")
                    # Wait before next poll
                    import time
                    time.sleep(poll_interval)
                    continue
                
                else:
                    debug_print(f"Unknown job status: {job_status}")
                    continue
            
            # If we get here, we've exceeded max poll attempts
            debug_print(f"Lesson generation timed out after {max_poll_attempts} polling attempts")
            debug_print(f"=== LESSON GENERATION TIMED OUT ===")
            return {"error": f"Lesson generation timed out after {max_poll_attempts * poll_interval} seconds"}
            
        except Exception as e:
            debug_print(f"Lesson generation failed with exception: {str(e)}")
            debug_print(f"=== LESSON GENERATION FAILED ===")
            return {"error": f"Lesson generation failed: {str(e)}"}