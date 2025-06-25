import re
import json
import os
import sqlite3
import requests
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import httpx
from fastapi import HTTPException
from pydantic import BaseModel
import uuid
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store for lesson generation jobs
lesson_jobs = {}

def fix_unicode_escapes(json_string):
    """Fix Unicode escape sequences in JSON string to make it parseable"""
    # Replace \uXXXX sequences with proper Unicode characters
    import codecs
    try:
        # First, try to decode the string as if it contains Unicode escapes
        decoded = codecs.decode(json_string, 'unicode_escape')
        return decoded
    except UnicodeDecodeError:
        # If that fails, return the original string
        return json_string

class TextGenerationRequest(BaseModel):
    prompt: str

class TextExplanationRequest(BaseModel):
    text: str

class TextAnalysisRequest(BaseModel):
    text: str

# Initialize extensions 
db = SQLAlchemy()
migrate = Migrate()

# Configuration
# Direct access to opea-docker services
OLLAMA_SERVER_URL = os.environ.get('OLLAMA_SERVER_URL', 'http://localhost:11434')
LLM_TEXT_URL = os.environ.get('LLM_TEXT_URL', 'http://localhost:11434')
GUARDRAILS_URL = os.environ.get('GUARDRAILS_URL', 'http://localhost:9400')
CHROMADB_URL = os.environ.get('CHROMADB_URL', 'http://localhost:8000')
TTS_URL = os.environ.get('TTS_URL', 'http://localhost:9200')
ASR_URL = os.environ.get('ASR_URL', 'http://localhost:9300')
LLM_VISION_URL = os.environ.get('LLM_VISION_URL', 'http://localhost:9101')
IMAGE_GEN_URL = os.environ.get('WAIFU_DIFFUSION_URL', 'http://localhost:9500')
EMBEDDINGS_URL = os.environ.get('EMBEDDINGS_URL', 'http://localhost:6000')

# Database path - use Docker path by default, fallback to local path for development
# In Docker: /app/data/shared_db/visual_novel.db (shared with other containers)
# In local dev: <project_root>/data/shared_db/visual_novel.db
DB_PATH = os.environ.get('DB_PATH', '/app/data/shared_db/visual_novel.db')

# LLM Service Configuration
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')

# Initialize database
def init_db():
    # Ensure the directory exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        lesson_id TEXT NOT NULL,
        scene_id TEXT NOT NULL,
        completed BOOLEAN DEFAULT 0,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, lesson_id, scene_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        japanese TEXT NOT NULL,
        reading TEXT,
        english TEXT,
        lesson_id TEXT,
        mastery_level INTEGER DEFAULT 0,
        last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def create_app(config_object=None):
    app = Flask(__name__)
    CORS(app)

    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        from config import Config
        app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from routes.game import game_bp
    from routes.images import images_bp
    from routes.translation import translation_bp
    from routes.tts import tts_bp

    app.register_blueprint(game_bp, url_prefix='/api/game')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(translation_bp, url_prefix='/api/translation')
    app.register_blueprint(tts_bp, url_prefix='/api/tts')

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'})
        
    # User routes
    @app.route('/api/user', methods=['POST'])
    def create_user():
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # First check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # User already exists, return the existing user's ID
                return jsonify({'id': existing_user[0], 'username': username}), 200
            
            # Create new user
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            conn.commit()
            user_id = cursor.lastrowid
            return jsonify({'id': user_id, 'username': username}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/progress/<int:user_id>', methods=['GET'])
    def get_progress(user_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT lesson_id, scene_id, completed, last_accessed FROM progress WHERE user_id = ?',
            (user_id,)
        )
        
        progress = [{
            'lesson_id': row[0],
            'scene_id': row[1],
            'completed': bool(row[2]),
            'last_accessed': row[3]
        } for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(progress)

    @app.route('/api/progress', methods=['POST'])
    def update_progress():
        data = request.json
        user_id = data.get('user_id')
        lesson_id = data.get('lesson_id')
        scene_id = data.get('scene_id')
        completed = data.get('completed', False)
        
        if not all([user_id, lesson_id, scene_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if progress record already exists
        cursor.execute(
            'SELECT id FROM progress WHERE user_id = ? AND lesson_id = ? AND scene_id = ?',
            (user_id, lesson_id, scene_id)
        )
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Update existing record
            cursor.execute(
                '''
                UPDATE progress 
                SET completed = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE user_id = ? AND lesson_id = ? AND scene_id = ?
                ''',
                (completed, user_id, lesson_id, scene_id)
            )
        else:
            # Insert new record
            cursor.execute(
                '''
                INSERT INTO progress (user_id, lesson_id, scene_id, completed, last_accessed)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (user_id, lesson_id, scene_id, completed)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})

    @app.route('/api/tts', methods=['POST'])
    def text_to_speech():
        data = request.json
        text = data.get('text')
        voice = data.get('voice', 'ja-JP')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        try:
            response = requests.post(
                f"{TTS_URL}/generate",
                json={'text': text, 'voice': voice}
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'TTS service error', 'details': response.text}), 500
        except requests.RequestException as e:
            return jsonify({'error': 'TTS service unavailable', 'details': str(e)}), 503

    @app.route('/api/speech-to-text', methods=['POST'])
    def speech_to_text():
        data = request.json
        audio_data = data.get('audio_data')
        language = data.get('language', 'ja-JP')
        
        if not audio_data:
            return jsonify({'error': 'Audio data is required'}), 400
        
        try:
            response = requests.post(
                f"{ASR_URL}/transcribe",
                json={
                    'audio_data': audio_data,
                    'language': language
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({'text': result.get('text', '')})
            else:
                return jsonify({'error': 'ASR service error', 'details': response.text}), 500
        except requests.RequestException as e:
            return jsonify({'error': 'ASR service unavailable', 'details': str(e)}), 503

    @app.route('/api/translate', methods=['POST'])
    def translate_text():
        data = request.json
        text = data.get('text')
        source_lang = data.get('source_lang', 'ja')
        target_lang = data.get('target_lang', 'en')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        try:
            response = requests.post(
                f"{LLM_TEXT_URL}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Provide only the translation, no explanations."
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    "stream": False
                },
                timeout=60  # Add 30-second timeout for translation
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("message", {}).get("content", "")
                return jsonify({"translated_text": translated_text})
            else:
                return jsonify({'error': 'Translation service error', 'details': response.text}), 500
        except requests.RequestException as e:
            return jsonify({'error': 'Translation service unavailable', 'details': str(e)}), 503

    @app.route('/api/generate-conversation', methods=['POST'])
    def generate_conversation():
        data = request.json
        context = data.get('context', '')
        characters = data.get('characters', [])
        grammar_points = data.get('grammar_points', [])
        vocabulary = data.get('vocabulary', [])
        num_exchanges = data.get('num_exchanges', 3)
        include_translations = data.get('include_translations', True)
        
        if not context or not characters:
            return jsonify({'error': 'Context and characters are required'}), 400
        
        # Construct a detailed prompt for the LLM
        prompt = f"""
        Generate a natural Japanese conversation at JLPT N5 level based on the following:
        
        CONTEXT: {context}
        
        CHARACTERS: {', '.join(characters)}
        
        GRAMMAR POINTS TO INCLUDE: {', '.join(grammar_points)}
        
        VOCABULARY TO INCLUDE: {', '.join(vocabulary)}
        
        INSTRUCTIONS:
        - Create a conversation with {num_exchanges} exchanges between characters
        - Use only JLPT N5 level grammar and vocabulary
        - Keep sentences short and simple
        - Use basic particles correctly (は, が, を, に, で, etc.)
        - Include at least one question and answer
        - Format the output as a JSON structure with speaker, japanese_text, and english_translation
        
        Example format:
        ```json
        {{
          "conversation": [
            {{
              "speaker": "Character1",
              "japanese_text": "こんにちは、お元気ですか？",
              "english_translation": "Hello, how are you?"
            }},
            {{
              "speaker": "Character2",
              "japanese_text": "はい、元気です。あなたは？",
              "english_translation": "Yes, I'm fine. And you?"
            }}
          ]
        }}
        ```
        
        Generate only the JSON response without any additional text.
        """
        
        try:
            response = requests.post(
                f"{LLM_TEXT_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a Japanese language teacher. Generate natural conversations that help students learn Japanese."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False
                },
                timeout=120  # Add 60-second timeout for conversation generation
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                # Try to extract and parse the JSON from the response
                try:
                    # The LLM might include markdown code blocks or extra text
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
                    
                    if json_match:
                        conversation_json = json.loads(json_match.group(1))
                    else:
                        # Try to find the first complete JSON object
                        # Look for the first { and find its matching }
                        start = content.find('{')
                        if start != -1:
                            # Find the matching closing brace
                            brace_count = 0
                            end = start
                            for i, char in enumerate(content[start:], start):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end = i + 1
                                        break
                            
                            if brace_count == 0:
                                json_content = content[start:end]
                                conversation_json = json.loads(json_content)
                            else:
                                # Fallback: try parsing the whole response as JSON
                                conversation_json = json.loads(content)
                        
                    return jsonify(conversation_json)
                except (json.JSONDecodeError, ValueError) as e:
                    # If JSON parsing fails, return the raw text
                    return jsonify({
                        'error': 'Failed to parse LLM response as JSON',
                        'raw_response': content
                    }), 422
            else:
                return jsonify({'error': 'Conversation generation error', 'details': response.text}), 500
        except requests.RequestException as e:
            return jsonify({'error': 'LLM service unavailable', 'details': str(e)}), 503

    @app.route('/api/generate-lesson', methods=['POST'])
    def generate_lesson():
        data = request.json
        topic = data.get('topic', '')
        grammar_points = data.get('grammar_points', [])
        vocabulary_focus = data.get('vocabulary_focus', [])
        lesson_number = data.get('lesson_number', 1)
        scene_setting = data.get('scene_setting', 'classroom')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Store the request data for processing
        lesson_jobs[job_id] = {
            'status': 'processing',
            'data': data,
            'result': None,
            'error': None
        }
        
        # Start the lesson generation in a background thread
        def generate_lesson_background():
            try:
                logging.info(f"DEBUG: Starting lesson generation for topic: {topic}")
                logging.info(f"DEBUG: Grammar points: {grammar_points}")
                logging.info(f"DEBUG: Vocabulary focus: {vocabulary_focus}")
                
                response = requests.post(
                    f"{LLM_TEXT_URL}/api/chat",
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a JSON generator. Return ONLY valid JSON, no other text."
                            },
                            {
                                "role": "user",
                                "content": f"Create a simple JLPT N5 lesson about {topic}.\n\n"
                                         f"Generate a complete lesson with Japanese vocabulary and dialogue.\n\n"
                                         f"Return ONLY valid JSON with this exact structure:\n"
                                         f"{{"
                                         f"  \"metadata\": {{"
                                         f"    \"title\": \"{topic}\","
                                         f"    \"objectives\": [\"Learn {topic.lower()}\", \"Practice Japanese\"]"
                                         f"  }},"
                                         f"  \"vocabulary\": ["
                                         f"    {{"
                                         f"      \"japanese\": \"こんにちは\","
                                         f"      \"reading\": \"konnichiwa\","
                                         f"      \"english\": \"Hello/Good afternoon\""
                                         f"    }},"
                                         f"    {{"
                                         f"      \"japanese\": \"おはようございます\","
                                         f"      \"reading\": \"ohayou gozaimasu\","
                                         f"      \"english\": \"Good morning\""
                                         f"    }}"
                                         f"  ],"
                                         f"  \"grammar_points\": ["
                                         f"    {{"
                                         f"      \"pattern\": \"は particle\","
                                         f"      \"explanation\": \"Topic marker used to indicate the subject of conversation\","
                                         f"      \"examples\": [\"私は学生です\", \"田中さんは先生です\"]"
                                         f"    }}"
                                         f"  ],"
                                         f"  \"dialogue_script\": ["
                                         f"    {{"
                                         f"      \"speaker\": \"Teacher\","
                                         f"      \"japanese\": \"おはようございます。今日は日本語の授業です。\","
                                         f"      \"english\": \"Good morning. Today is Japanese class.\""
                                         f"    }},"
                                         f"    {{"
                                         f"      \"speaker\": \"Student\","
                                         f"      \"japanese\": \"おはようございます。よろしくお願いします。\","
                                         f"      \"english\": \"Good morning. Nice to meet you.\""
                                         f"    }}"
                                         f"  ],"
                                         f"  \"exercises\": ["
                                         f"    {{"
                                         f"      \"question\": \"Complete: 私は___です\","
                                         f"      \"options\": [\"学生\", \"先生\", \"医者\"],"
                                         f"      \"correct_answer\": \"学生\""
                                         f"    }}"
                                         f"  ]"
                                         f"}}\n\n"
                                         f"Fill ALL fields with appropriate content for the topic '{topic}'. Do NOT leave any fields empty."
                            }
                        ],
                        "stream": False
                    },
                    timeout=120,  # Increased timeout to 120 seconds
                    headers={'Content-Type': 'application/json'}
                )
                
                logging.info(f"DEBUG: LLM response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("message", {}).get("content", "")
                    
                    logging.info(f"DEBUG: Raw LLM response content length: {len(content)}")
                    logging.info(f"DEBUG: Raw LLM response content: {content[:2000]}...")  # Increased to 2000 chars
                    
                    # Try to extract and parse the JSON from the response
                    try:
                        # The LLM might include markdown code blocks or extra text
                        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
                        
                        if json_match:
                            json_content = fix_unicode_escapes(json_match.group(1))
                            lesson_json = json.loads(json_content)
                            logging.info(f"DEBUG: Extracted JSON from code block")
                        else:
                            # Try to find the first complete JSON object
                            # Look for the first { and find its matching }
                            start = content.find('{')
                            if start != -1:
                                # Find the matching closing brace
                                brace_count = 0
                                end = start
                                for i, char in enumerate(content[start:], start):
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end = i + 1
                                            break
                                
                                if brace_count == 0:
                                    json_content = content[start:end]
                                    json_content = fix_unicode_escapes(json_content)
                                    logging.info(f"DEBUG: Extracted JSON content length: {len(json_content)}")
                                    logging.info(f"DEBUG: Extracted JSON content: {json_content}")
                                    
                                    # Try to parse the JSON
                                    try:
                                        lesson_json = json.loads(json_content)
                                        logging.info(f"DEBUG: Extracted JSON from content (start={start}, end={end})")
                                    except json.JSONDecodeError as e:
                                        logging.info(f"DEBUG: JSON decode error: {str(e)}")
                                        # Try to fix common JSON issues
                                        # Remove trailing commas
                                        json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
                                        # Try parsing again
                                        lesson_json = json.loads(json_content)
                                        logging.info(f"DEBUG: Successfully parsed after fixing trailing commas")
                                else:
                                    logging.info(f"DEBUG: Incomplete JSON - brace count: {brace_count}")
                                    logging.info(f"DEBUG: Content up to last complete brace: {content[start:end]}")
                                    # Try to complete the JSON by adding missing closing braces
                                    incomplete_content = content[start:end]
                                    incomplete_content = fix_unicode_escapes(incomplete_content)
                                    missing_braces = brace_count
                                    completed_content = incomplete_content + "}" * missing_braces
                                    logging.info(f"DEBUG: Attempting to complete JSON with {missing_braces} closing braces")
                                    
                                    try:
                                        lesson_json = json.loads(completed_content)
                                        logging.info(f"DEBUG: Successfully parsed completed JSON")
                                    except json.JSONDecodeError as e:
                                        logging.info(f"DEBUG: Failed to parse completed JSON: {str(e)}")
                                        # Try to create a minimal valid JSON as fallback
                                        lesson_json = {
                                            "metadata": {"title": topic, "objectives": [f"Learn {topic.lower()}", "Practice Japanese"]},
                                            "vocabulary": [{"japanese": "こんにちは", "reading": "konnichiwa", "english": "Hello"}],
                                            "grammar_points": [{"pattern": "は particle", "explanation": "Topic marker", "examples": ["私は学生です"]}],
                                            "dialogue_script": [{"speaker": "Teacher", "japanese": "こんにちは", "english": "Hello"}],
                                            "exercises": [{"question": "Complete: 私は___です", "options": ["学生", "先生"], "correct_answer": "学生"}]
                                        }
                                        logging.info(f"DEBUG: Using fallback JSON structure")
                            else:
                                logging.info(f"DEBUG: No JSON object found in response")
                                # Fallback: try parsing the whole response as JSON
                                content = fix_unicode_escapes(content)
                                try:
                                    lesson_json = json.loads(content)
                                    logging.info(f"DEBUG: Parsed entire response as JSON")
                                except json.JSONDecodeError:
                                    # Create fallback JSON
                                    lesson_json = {
                                        "metadata": {"title": topic, "objectives": [f"Learn {topic.lower()}", "Practice Japanese"]},
                                        "vocabulary": [{"japanese": "こんにちは", "reading": "konnichiwa", "english": "Hello"}],
                                        "grammar_points": [{"pattern": "は particle", "explanation": "Topic marker", "examples": ["私は学生です"]}],
                                        "dialogue_script": [{"speaker": "Teacher", "japanese": "こんにちは", "english": "Hello"}],
                                        "exercises": [{"question": "Complete: 私は___です", "options": ["学生", "先生"], "correct_answer": "学生"}]
                                    }
                                    logging.info(f"DEBUG: Using fallback JSON structure")
                        
                        # Validate and fix the lesson structure
                        if "dialogue_script" in lesson_json:
                            fixed_dialogue = []
                            for entry in lesson_json["dialogue_script"]:
                                if isinstance(entry, dict):
                                    # Ensure all required fields are present
                                    fixed_entry = {
                                        "speaker": entry.get("speaker", "Unknown"),
                                        "japanese": entry.get("japanese", ""),
                                        "english": entry.get("english", "")
                                    }
                                    fixed_dialogue.append(fixed_entry)
                                else:
                                    logging.info(f"DEBUG: Skipping invalid dialogue entry: {entry}")
                            lesson_json["dialogue_script"] = fixed_dialogue
                            logging.info(f"DEBUG: Fixed dialogue script with {len(fixed_dialogue)} entries")
                        
                        logging.info(f"DEBUG: Parsed lesson JSON keys: {list(lesson_json.keys())}")
                        logging.info(f"DEBUG: Vocabulary count: {len(lesson_json.get('vocabulary', []))}")
                        logging.info(f"DEBUG: Dialogue count: {len(lesson_json.get('dialogue_script', []))}")
                        
                        lesson_jobs[job_id]['status'] = 'completed'
                        lesson_jobs[job_id]['result'] = lesson_json
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logging.info(f"DEBUG: JSON parsing error: {str(e)}")
                        lesson_jobs[job_id]['status'] = 'error'
                        lesson_jobs[job_id]['error'] = f'Failed to parse LLM response as JSON: {str(e)}'
                else:
                    logging.info(f"DEBUG: LLM service error: {response.text}")
                    lesson_jobs[job_id]['status'] = 'error'
                    lesson_jobs[job_id]['error'] = f'LLM service error: {response.text}'
                    
            except Exception as e:
                logging.info(f"DEBUG: Exception in lesson generation: {str(e)}")
                lesson_jobs[job_id]['status'] = 'error'
                lesson_jobs[job_id]['error'] = str(e)
        
        # Start the background thread
        thread = threading.Thread(target=generate_lesson_background)
        thread.daemon = True
        thread.start()
        
        # Return immediately with the job ID
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Lesson generation started. Use the job_id to check status.'
        })
    
    @app.route('/api/lesson-status/<job_id>', methods=['GET'])
    def get_lesson_status(job_id):
        if job_id not in lesson_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = lesson_jobs[job_id]
        return jsonify({
            'job_id': job_id,
            'status': job['status'],
            'result': job['result'],
            'error': job['error']
        })

    @app.route('/api/vocabulary', methods=['POST'])
    def add_vocabulary():
        data = request.json
        user_id = data.get('user_id')
        japanese = data.get('japanese')
        reading = data.get('reading')
        english = data.get('english')
        lesson_id = data.get('lesson_id')
        
        if not all([user_id, japanese]):
            return jsonify({'error': 'User ID and Japanese text are required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''
                INSERT INTO vocabulary (user_id, japanese, reading, english, lesson_id)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, japanese, reading, english, lesson_id)
            )
            
            conn.commit()
            vocab_id = cursor.lastrowid
            
            return jsonify({
                'id': vocab_id,
                'user_id': user_id,
                'japanese': japanese,
                'reading': reading,
                'english': english,
                'lesson_id': lesson_id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/vocabulary/<int:user_id>', methods=['GET'])
    def get_vocabulary(user_id):
        lesson_id = request.args.get('lesson_id')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            if lesson_id:
                cursor.execute(
                    'SELECT id, japanese, reading, english, lesson_id, mastery_level FROM vocabulary WHERE user_id = ? AND lesson_id = ?',
                    (user_id, lesson_id)
                )
            else:
                cursor.execute(
                    'SELECT id, japanese, reading, english, lesson_id, mastery_level FROM vocabulary WHERE user_id = ?',
                    (user_id,)
                )
            
            vocabulary = [{
                'id': row[0],
                'japanese': row[1],
                'reading': row[2],
                'english': row[3],
                'lesson_id': row[4],
                'mastery_level': row[5]
            } for row in cursor.fetchall()]
            
            return jsonify(vocabulary)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/image/generate', methods=['POST'])
    def generate_image():
        data = request.json
        prompt = data.get('prompt')
        negative_prompt = data.get('negative_prompt')
        width = data.get('width', 512)
        height = data.get('height', 512)
        style = data.get('style', 'anime')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        try:
            response = requests.post(
                IMAGE_GEN_URL,
                json={
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'width': width,
                    'height': height,
                    'style': style
                }
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Image generation error', 'details': response.text}), 500
        except requests.RequestException as e:
            return jsonify({'error': 'Image generation service unavailable', 'details': str(e)}), 503

    @app.post("/generate")
    async def generate_text(request: TextGenerationRequest):
        try:
            response = await httpx.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "user", "content": request.prompt}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return {"text": result.get("message", {}).get("content", "")}
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/explain")
    async def explain_text(request: TextExplanationRequest):
        try:
            response = await httpx.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that explains Japanese text in simple terms."},
                        {"role": "user", "content": f"Please explain this Japanese text in simple terms: {request.text}"}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return {"explanation": result.get("message", {}).get("content", "")}
        except Exception as e:
            logger.error(f"Error explaining text: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/analyze")
    async def analyze_text(request: TextAnalysisRequest):
        try:
            response = await httpx.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that analyzes Japanese text for grammar and vocabulary."},
                        {"role": "user", "content": f"Please analyze this Japanese text: {request.text}"}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return {"analysis": result.get("message", {}).get("content", "")}
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app

# Application entry point
if __name__ == '__main__':
    from config import Config
    app = create_app(Config)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Get port from environment or config
    port = int(os.environ.get('PORT', app.config.get('PORT', 8001)))
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Starting server on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)