# API communication module for Japanese Learning Visual Novel
# This module provides access to services through the Flask API gateway

import requests
import json
import os
import base64
from io import BytesIO
import tempfile
import time
import threading

# Global variable for emscripten module (will be set if available)
emscripten = None

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    # Try multiple possible paths for the .env file
    # The .env file is in the visual-novel directory, but the game might be running from different locations
    possible_paths = [
        # Relative to current file location
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
        # Relative to current working directory
        '.env',
        # Absolute paths that might work
        '/home/sage/free-genai-bootcamp-2025/visual-novel/.env',
        '/visual-novel/.env',
        # Try going up directories from current location
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), '..', '.env'),
        os.path.join(os.getcwd(), '..', '..', '.env'),
    ]
    
    env_path = None
    for path in possible_paths:
        print(f"DEBUG: Checking for .env file at: {path}")
        if os.path.exists(path):
            env_path = path
            break
    
    if env_path:
        print(f"DEBUG: .env file found at: {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"DEBUG: Set {key} = {value}")
        print(f"DEBUG: Loaded environment variables from {env_path}")
    else:
        print(f"DEBUG: .env file not found in any of the checked locations")
        print(f"DEBUG: Checked paths: {possible_paths}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Current file location: {__file__}")
        
        # Set fallback values for web builds
        if 'FLASK_SERVER_URL' not in os.environ:
            # For web builds, we need to use the nginx server on port 8001
            # This is the server that serves the Ren'Py web app and proxies API calls
            os.environ['FLASK_SERVER_URL'] = 'http://localhost:8001'
            print("DEBUG: Set fallback FLASK_SERVER_URL = http://localhost:8001 for web build")
        
        # Set other essential environment variables for web builds
        if 'SECRET_KEY' not in os.environ:
            os.environ['SECRET_KEY'] = 'your-secret-key'
        if 'FLASK_DEBUG' not in os.environ:
            os.environ['FLASK_DEBUG'] = 'true'
        if 'USE_REMOTE_DB' not in os.environ:
            os.environ['USE_REMOTE_DB'] = 'true'

# Load environment variables
load_env_file()

# Try to import emscripten if available
try:
    import emscripten
    print("DEBUG: Successfully imported emscripten module")
except ImportError:
    print("DEBUG: emscripten module not available")
    emscripten = None

# Cache for web browser detection to avoid timing issues
_web_browser_cache = None

# API endpoints configuration
# For web browser compatibility, we need to handle relative URLs properly

def is_web_browser():
    """Detect if we're running in a web browser environment"""
    global _web_browser_cache
    
    # Return cached result if available
    if _web_browser_cache is not None:
        return _web_browser_cache
    
    try:
        # Most reliable: Emscripten is only present in web builds
        if emscripten is not None:
            print("DEBUG: Detected web browser via emscripten import (most reliable)")
            _web_browser_cache = True
            return True
        
        import platform
        
        # Manual override for known web environment (from previous logs)
        # We know this is running in Emscripten web environment
        if 'Emscripten' in str(platform) or 'WebKit' in str(platform):
            print("DEBUG: Manual override - detected web browser from platform info")
            _web_browser_cache = True
            return True
        
        # Use Ren'Py's built-in platform detection
        import renpy
        
        # Check if we're on the web platform
        if hasattr(renpy, 'variant'):
            if renpy.variant("web"):
                print("DEBUG: Detected web platform via renpy.variant('web')")
                _web_browser_cache = True
                return True
        
        # Check for Emscripten environment (web browser)
        import sys
        
        # Check multiple indicators of web browser environment
        platform_str = str(platform).lower()
        sys_str = str(sys).lower()
        
        # Look for Emscripten indicators
        if 'emscripten' in platform_str or 'emscripten' in sys_str:
            print("DEBUG: Detected web browser via emscripten in platform/sys")
            _web_browser_cache = True
            return True
            
        # Check for WebKit/WebGL renderer (from the log we can see this)
        if 'webkit' in platform_str or 'webgl' in platform_str:
            print("DEBUG: Detected web browser via webkit/webgl in platform")
            _web_browser_cache = True
            return True
            
        # Check if we're running in a browser environment
        if hasattr(sys, 'get_platform'):
            platform_name = sys.get_platform().lower()
            if 'emscripten' in platform_name:
                print("DEBUG: Detected web browser via sys.get_platform()")
                _web_browser_cache = True
                return True
        
        # Check for specific Ren'Py web indicators
        try:
            # Check if we're in a web build by looking for web-specific modules
            if hasattr(renpy, 'web'):
                print("DEBUG: Detected web browser via renpy.web")
                _web_browser_cache = True
                return True
        except:
            pass
        
        # Check environment variables that might indicate web environment
        if 'RENPY_WEB' in os.environ or 'EMSCRIPTEN' in os.environ:
            print("DEBUG: Detected web browser via environment variables")
            _web_browser_cache = True
            return True
                
        print("DEBUG: No web browser indicators found")
        _web_browser_cache = False
        return False
    except Exception as e:
        print(f"DEBUG: Error in web browser detection: {str(e)}")
        # If we can't detect, try a few more methods
        try:
            import platform
            if 'emscripten' in str(platform).lower():
                print("DEBUG: Detected web browser via platform fallback")
                _web_browser_cache = True
                return True
        except:
            pass
        _web_browser_cache = False
        return False

def refresh_web_browser_detection():
    """Force refresh the web browser detection cache"""
    global _web_browser_cache
    _web_browser_cache = None
    return is_web_browser()

def get_base_url():
    """Get the base URL for API requests"""
    # Try to get from environment first
    flask_url = os.environ.get('FLASK_SERVER_URL', '')
    print(f"DEBUG: get_base_url: FLASK_SERVER_URL from env = '{flask_url}'")
    if flask_url:
        return flask_url.rstrip('/')
    
    # If no environment variable is set and we're in a web browser,
    # we need to use the nginx server on port 8001
    if is_web_browser():
        # For web browser, use the nginx server on port 8001
        # The nginx server is serving the Ren'Py app and proxying API calls
        print("DEBUG: get_base_url: Using http://localhost:8001 for web browser")
        return "http://localhost:8001"
    
    # For local development, default to localhost
    print("DEBUG: get_base_url: Using http://localhost:8080 for local development")
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
print(f"DEBUG: FLASK_SERVER_URL = {FLASK_SERVER_URL}")
print(f"DEBUG: LESSON_GENERATION_ENDPOINT = {LESSON_GENERATION_ENDPOINT}")
print(f"DEBUG: GAME_API_BASE_URL = {GAME_API_BASE_URL}")
print(f"DEBUG: Is web browser: {is_web_browser()}")
print(f"DEBUG: Environment FLASK_SERVER_URL: {os.environ.get('FLASK_SERVER_URL', 'NOT_SET')}")

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
    
    print(f"DEBUG: Reinitialized endpoints - FLASK_SERVER_URL = {FLASK_SERVER_URL}")
    print(f"DEBUG: Reinitialized endpoints - Is web browser: {is_web_browser()}")

def make_web_request(method, url, data=None, headers=None):
    """Make HTTP request using appropriate method for the environment"""
    # Check if we need to reinitialize endpoints (in case web browser detection changed)
    if is_web_browser() and FLASK_SERVER_URL != get_base_url():
        print("DEBUG: Web browser detection changed, reinitializing endpoints")
        reinitialize_endpoints()
    
    if is_web_browser():
        print("DEBUG: Web browser detected, trying multiple HTTP request methods")
        
        # Method 1: Try using emscripten if available
        if emscripten is not None:
            print("DEBUG: Trying emscripten-based HTTP request")
            try:
                # Use simple synchronous XMLHttpRequest with timeout
                print("DEBUG: Using simple synchronous XMLHttpRequest")
                
                # Convert data to JSON string if provided
                if data is not None:
                    data_str = json.dumps(data)
                else:
                    data_str = ""
                
                print(f"DEBUG: Making simple XMLHttpRequest: {method} {url}")
                
                # Use a very simple synchronous approach
                js_code = f'''
                (function() {{
                    try {{
                        var xhr = new XMLHttpRequest();
                        xhr.timeout = 5000; // 5 second timeout
                        xhr.open("{method.upper()}", "{url}", false); // synchronous
                        xhr.setRequestHeader("Content-Type", "application/json");
                        xhr.setRequestHeader("Accept", "application/json");
                        xhr.send("{data_str}" || null);
                        return xhr.status + " " + xhr.responseText;
                    }} catch (error) {{
                        return "ERROR " + error.message;
                    }}
                }})()
                '''
                
                result = emscripten.run_script_string(js_code)
                print(f"DEBUG: Simple XMLHttpRequest result: {result}")
                
                if result and not result.startswith('ERROR'):
                    # Parse the result (format: "status_code response_text")
                    parts = result.split(' ', 1)
                    if len(parts) >= 2:
                        status_code = int(parts[0])
                        response_text = parts[1]
                        
                        print(f"DEBUG: Simple XMLHttpRequest success: status={status_code}, text={response_text[:100]}...")
                        
                        return type('Response', (), {
                            'status_code': status_code,
                            'text': response_text,
                            'json': lambda *args: json.loads(response_text) if response_text else {}
                        })()
                else:
                    print(f"DEBUG: Simple XMLHttpRequest error: {result}")
                    raise Exception(f"Simple XMLHttpRequest failed: {result}")
                    
            except Exception as js_error:
                print(f"DEBUG: emscripten-based request failed: {str(js_error)}")
                # Continue to next method
        
        # Method 2: Try using Ren'Py's built-in web functionality
        print("DEBUG: Trying Ren'Py built-in web functionality")
        try:
            import renpy
            
            # Check if renpy has web-specific functionality
            if hasattr(renpy, 'web'):
                print("DEBUG: Found renpy.web module")
                # Try to use renpy.web functionality if available
                pass
            
            # Check if there's a way to access JavaScript functions through renpy
            if hasattr(renpy, 'execute'):
                print("DEBUG: Found renpy.execute, trying to use it")
                # Try to execute JavaScript through renpy
                pass
                
        except Exception as renpy_error:
            print(f"DEBUG: Ren'Py web functionality failed: {str(renpy_error)}")
        
        # Method 3: Try using a different approach to access JavaScript
        print("DEBUG: Trying alternative JavaScript access method")
        try:
            # Try to access JavaScript functions through a different method
            # This might work if the emscripten module is available but not imported correctly
            import sys
            
            # Check if we can access JavaScript through sys.modules
            if 'emscripten' in sys.modules:
                print("DEBUG: emscripten found in sys.modules")
                emscripten_module = sys.modules['emscripten']
                if hasattr(emscripten_module, 'run_script_string'):
                    print("DEBUG: Using emscripten from sys.modules")
                    # Try the same approach as above but with the module from sys.modules
                    pass
                    
        except Exception as alt_error:
            print(f"DEBUG: Alternative JavaScript access failed: {str(alt_error)}")
        
        # Method 4: Try using fetchFile directly if available
        print("DEBUG: Trying fetchFile directly")
        try:
            # Convert data to JSON string if provided
            if data is not None:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    json.dump(data, f)
                    data_file = f.name
            else:
                data_file = ""  # explicitly use an empty string for no data
            
            print(f"DEBUG: Calling fetchFile with data_file={data_file}")
            
            # Try to access fetchFile through different methods
            fetch_id = None
            
            # Try method 1: emscripten if available
            if emscripten is not None:
                try:
                    fetch_id = emscripten.run_script_int(f'fetchFile("{method}", "{url}", "{data_file}", "", "application/json", \'{json.dumps(headers)}\')')
                    print(f"DEBUG: fetchFile returned ID: {fetch_id}")
                except Exception as e:
                    print(f"DEBUG: emscripten fetchFile failed: {str(e)}")
            
            # Try method 2: sys.modules if emscripten is there
            if fetch_id is None:
                try:
                    import sys
                    if 'emscripten' in sys.modules:
                        emscripten_module = sys.modules['emscripten']
                        if hasattr(emscripten_module, 'run_script_int'):
                            fetch_id = emscripten_module.run_script_int(f'fetchFile("{method}", "{url}", "{data_file}", "", "application/json", \'{json.dumps(headers)}\')')
                            print(f"DEBUG: fetchFile from sys.modules returned ID: {fetch_id}")
                except Exception as e:
                    print(f"DEBUG: sys.modules fetchFile failed: {str(e)}")
            
            if fetch_id is not None and fetch_id != 0:
                # Wait for result with timeout
                import time
                start_time = time.time()
                timeout = 5  # Reduced timeout for faster debugging
                
                while True:
                    if time.time() - start_time > timeout:
                        print(f"DEBUG: fetchFile timeout after {timeout} seconds")
                        raise Exception(f"HTTP request timeout after {timeout} seconds")
                    
                    try:
                        # Try to get result through emscripten
                        if emscripten is not None:
                            result = emscripten.run_script_string(f'fetchFileResult({fetch_id})')
                        else:
                            # Try through sys.modules
                            import sys
                            if 'emscripten' in sys.modules:
                                emscripten_module = sys.modules['emscripten']
                                result = emscripten_module.run_script_string(f'fetchFileResult({fetch_id})')
                            else:
                                result = None
                        
                        print(f"DEBUG: fetchFileResult returned: {result}")
                        
                        if result is None:
                            print("DEBUG: fetchFileResult returned None, waiting...")
                            time.sleep(0.1)
                            continue
                        
                        if not result.startswith('PENDING'):
                            break
                    except Exception as e:
                        print(f"DEBUG: Error calling fetchFileResult: {str(e)}")
                        time.sleep(0.1)
                        continue
                    
                    time.sleep(0.1)
                
                # Parse result
                if result.startswith('OK'):
                    # Success - extract status code and response
                    parts = result.split(' ', 2)
                    status_code = int(parts[1])
                    status_text = parts[2] if len(parts) > 2 else ''
                    
                    print(f"DEBUG: fetchFile success: status={status_code}, text={status_text[:100]}...")
                    
                    # Return a response object similar to requests
                    return type('Response', (), {
                        'status_code': status_code,
                        'text': status_text,
                        'json': lambda *args: json.loads(status_text) if status_text else {}
                    })()
                else:
                    # Error
                    print(f"DEBUG: fetchFile error: {result}")
                    raise Exception(f"HTTP request failed: {result}")
            else:
                print("DEBUG: fetchFile returned None/0, fetchFile not available")
                raise Exception("fetchFile not available")
                
        except Exception as fetchfile_error:
            print(f"DEBUG: fetchFile approach failed: {str(fetchfile_error)}")
        
        # If all methods fail, return error response
        print("DEBUG: All web request methods failed, returning error response")
        return type('Response', (), {
            'status_code': 503,
            'text': '{"error": "No working HTTP request method available in web environment"}',
            'json': lambda *args: {"error": "No working HTTP request method available in web environment"}
        })()
    else:
        # Use requests library for local development
        if method.upper() == 'GET':
            return requests.get(url, headers=headers, timeout=5)
        elif method.upper() == 'POST':
            return requests.post(url, json=data, headers=headers, timeout=5)
        else:
            raise Exception(f"Unsupported HTTP method: {method}")

class APIService:
    """Centralized API service for all external calls"""
    
    @staticmethod
    def test_ollama_connection():
        """Test if Flask server is reachable"""
        try:
            health_url = f"{GAME_API_BASE_URL}/health"
            print(f"DEBUG: Testing connection to {health_url}")
            
            # For web environments, don't use threading (not supported in Emscripten)
            if is_web_browser():
                print("DEBUG: Web environment detected, using direct request without threading")
                try:
                    response = make_web_request('GET', health_url)
                    print(f"DEBUG: Flask server connection test status: {response.status_code}")
                    return response.status_code == 200
                except Exception as e:
                    print(f"DEBUG: Web request failed: {str(e)}")
                    print("DEBUG: Server connection failed - servers are required for game functionality")
                    return False
            else:
                # For local development, use threading with timeout
                import threading
                import time
                
                result = [None]
                exception = [None]
                
                def make_request():
                    try:
                        response = make_web_request('GET', health_url)
                        result[0] = response
                    except Exception as e:
                        exception[0] = e
                
                # Start the request in a separate thread
                thread = threading.Thread(target=make_request)
                thread.daemon = True
                thread.start()
                
                # Wait for up to 5 seconds
                timeout = 5
                start_time = time.time()
                while thread.is_alive() and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if thread.is_alive():
                    print(f"DEBUG: Connection test timed out after {timeout} seconds")
                    print("DEBUG: Server connection failed - servers are required for game functionality")
                    return False
                
                if exception[0]:
                    raise exception[0]
                
                response = result[0]
                print(f"DEBUG: Flask server connection test status: {response.status_code}")
                return response.status_code == 200
                
        except Exception as e:
            print(f"DEBUG: Flask server connection test failed: {str(e)}")
            print("DEBUG: Server connection failed - servers are required for game functionality")
            return False
    
    @staticmethod
    def create_user(username):
        """Create a new user in the database"""
        try:
            user_url = f"{GAME_API_BASE_URL}/user"
            print(f"DEBUG: Creating user with URL: {user_url}")
            print(f"DEBUG: Username: {username}")
            response = make_web_request('POST', user_url, {"username": username})
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")
            if response.status_code in [200, 201]:  # 200 for existing user, 201 for new user
                result = response.json()
                user_id = result.get("id")
                print(f"User creation successful: {result}")
                return user_id
            else:
                print(f"Failed to create user: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Failed to create user: {str(e)}")
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
            print(f"Failed to save progress: {str(e)}")
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
            print(f"Translation failed: {str(e)}")
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
                # We need to save it to a file and return the path
                audio_data = base64.b64decode(result["audio"])
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    temp_path = temp_file.name
                
                return temp_path
            return None
        except Exception as e:
            print(f"TTS failed: {str(e)}")
            return None
    
    @staticmethod
    def speech_to_text(audio_path, language="ja-JP"):
        """Convert speech to text using ASR service"""
        try:
            with open(audio_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
            
            asr_url = f"{GAME_API_BASE_URL}/speech-to-text"
            
            response = make_web_request('POST', asr_url, {
                "audio_data": audio_data,
                "language": language
            })
            
            result = response.json()
            return result.get("text", "")
        except Exception as e:
            print(f"ASR failed: {str(e)}")
            return ""
    @staticmethod
    def add_vocabulary(user_id, japanese, reading=None, english=None, lesson_id=None):
        """Add vocabulary to player's list"""
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
            print(f"Failed to add vocabulary: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_image(prompt, image_type="background", negative_prompt=None, 
                      width=512, height=512, style="anime"):
        """Generate an image using the image generation service
        
        Args:
            prompt: The text prompt for image generation
            image_type: Either 'background' or 'character' to determine save location
            negative_prompt: What to avoid in the image
            width: Image width
            height: Image height
            style: Image style (anime, realistic, etc.)
            
        Returns:
            Path to the generated image or None if generation failed
        """
        try:
            image_url = IMAGE_GEN_ENDPOINT
            
            response = make_web_request('POST', image_url, {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "style": style,
                "return_format": "base64"
            })
            
            if response.status_code != 200:
                print(f"Image generation failed: {response.text}")
                return None
                
            result = response.json()
            
            if "image" in result:
                # Save the base64 image to a file
                image_data = base64.b64decode(result["image"])
                
                # Determine the save directory based on image_type
                if image_type.lower() == "character":
                    save_dir = "images/characters"
                else:  # Default to backgrounds
                    save_dir = "images/backgrounds"
                
                # Create directory if it doesn't exist
                os.makedirs(save_dir, exist_ok=True)
                
                # Create a safe filename from the prompt
                safe_filename = "".join(c for c in prompt if c.isalnum() or c in " _-").strip()
                safe_filename = safe_filename.replace(" ", "_")[:30]
                
                # Save the image
                image_path = f"{save_dir}/{safe_filename}.png"
                
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                # Log the saved image
                print(f"Generated image saved to: {image_path}")
                
                return image_path
            else:
                print("Image generation failed: No image data received")
                return None
        except Exception as e:
            print(f"Image generation failed: {str(e)}")
            return None
            
    @staticmethod
    def generate_conversation(context, characters, grammar_points=None, vocabulary=None, num_exchanges=3):
        """Generate a dynamic conversation using the LLM"""
        try:
            if grammar_points is None:
                grammar_points = []
            if vocabulary is None:
                vocabulary = []
                
            # Create a prompt for conversation generation
            prompt = f"""
            Generate a natural Japanese conversation with the following context:
            Context: {context}
            Characters: {', '.join(characters)}
            Grammar points to include: {', '.join(grammar_points)}
            Vocabulary to include: {', '.join(vocabulary)}
            Number of exchanges: {num_exchanges}
            
            Please provide the conversation in JSON format with the following structure:
            {{
                "conversation": [
                    {{"speaker": "Character1", "japanese": "こんにちは", "english": "Hello"}},
                    {{"speaker": "Character2", "japanese": "こんにちは", "english": "Hello"}}
                ]
            }}
            """
            
            conversation_url = CONVERSATION_ENDPOINT
            
            response = make_web_request('POST', conversation_url, {
                "context": context,
                "characters": characters,
                "grammar_points": grammar_points,
                "vocabulary": vocabulary,
                "num_exchanges": num_exchanges
            })
            
            if response.status_code != 200:
                print(f"Conversation generation failed: {response.text}")
                return None
                
            result = response.json()
            conversation_data = result.get("conversation", [])
            
            # The Flask server should return the conversation data directly
            if conversation_data:
                return conversation_data
            else:
                print("Unexpected response format from conversation generator")
                return None
        except Exception as e:
            print(f"Failed to generate conversation: {str(e)}")
            return None
            
    @staticmethod
    def generate_lesson(topic, grammar_points=None, vocabulary_focus=None, lesson_number=1, scene_setting="classroom"):
        """Generate a complete lesson using the LLM"""
        try:
            if grammar_points is None:
                grammar_points = []
            if vocabulary_focus is None:
                vocabulary_focus = []
                
            print(f"DEBUG: Generating lesson for topic: {topic}")
            print(f"DEBUG: Using FLASK_SERVER_URL: {FLASK_SERVER_URL}")
                
            # Create a prompt for lesson generation
            prompt = f"""
            Generate a complete Japanese lesson with the following details:
            Topic: {topic}
            Lesson Number: {lesson_number}
            Scene Setting: {scene_setting}
            Grammar points to cover: {', '.join(grammar_points)}
            Vocabulary focus: {', '.join(vocabulary_focus)}
            
            Please provide the lesson in JSON format with the following structure:
            {{
                "metadata": {{
                    "title": "Lesson Title",
                    "topic": "{topic}",
                    "objectives": ["objective1", "objective2", "objective3"]
                }},
                "grammar_points": ["grammar1", "grammar2"],
                "vocabulary": [
                    {{"japanese": "こんにちは", "reading": "konnichiwa", "english": "hello"}}
                ],
                "dialogue_script": [
                    {{"speaker": "Sensei", "text": "こんにちは", "translation": "Hello"}},
                    {{"speaker": "Player", "text": "こんにちは", "translation": "Hello"}}
                ]
            }}
            """
            
            # Use the correct endpoint URL
            lesson_url = LESSON_GENERATION_ENDPOINT
            
            print(f"DEBUG: Sending request to {lesson_url}")
                
            response = make_web_request('POST', lesson_url, {
                "topic": topic,
                "grammar_points": grammar_points,
                "vocabulary_focus": vocabulary_focus,
                "lesson_number": lesson_number,
                "scene_setting": scene_setting
            })
            
            print(f"DEBUG: Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Lesson generation failed: {response.text}")
                return None
                
            result = response.json()
            lesson_data = result.get("lesson", {})
            
            print(f"DEBUG: Raw response content: {lesson_data}")
            
            # The Flask server already returns the lesson data in the correct format
            if lesson_data:
                print(f"DEBUG: Successfully received lesson data")
                return lesson_data
            else:
                print("Lesson generation failed: No lesson data received")
                return None
        except Exception as e:
            print(f"Lesson generation failed: {str(e)}")
            return None