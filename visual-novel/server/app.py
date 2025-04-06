import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import requests

app = Flask(__name__)
CORS(app)

# Configuration
LLM_TEXT_URL = os.environ.get('LLM_TEXT_URL', 'http://llm_text:9000')
TTS_URL = os.environ.get('TTS_URL', 'http://tts:9200')
ASR_URL = os.environ.get('ASR_URL', 'http://asr:9300')
LLM_VISION_URL = os.environ.get('LLM_VISION_URL', 'http://llm-vision:9100')
EMBEDDINGS_URL = os.environ.get('EMBEDDINGS_URL', 'http://embeddings:6000')
OPENVINO_URL = os.environ.get('OPENVINO_URL', 'http://vn-openvino-service:8081')
DB_PATH = os.environ.get('DB_PATH', '/app/db/visual_novel.db')

# Initialize database
def init_db():
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
        FOREIGN KEY (user_id) REFERENCES users(id)
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

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({'id': user_id, 'username': username}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
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
    
    cursor.execute(
        '''
        INSERT INTO progress (user_id, lesson_id, scene_id, completed, last_accessed)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, lesson_id, scene_id) 
        DO UPDATE SET completed = ?, last_accessed = CURRENT_TIMESTAMP
        ''',
        (user_id, lesson_id, scene_id, completed, completed)
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
            f"{TTS_URL}/tts",
            json={'text': text, 'voice': voice}
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'TTS service error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'TTS service unavailable', 'details': str(e)}), 503

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
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': f"Translate the following {source_lang} text to {target_lang}: {text}",
                'max_tokens': 1000
            }
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Translation service error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'Translation service unavailable', 'details': str(e)}), 503

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')
    scene_type = data.get('scene_type', 'background')  # background, character, etc.
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # First, enhance the prompt using LLM
        llm_response = requests.post(
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': f"Enhance this image generation prompt for a Japanese visual novel scene: {prompt}",
                'max_tokens': 500
            }
        )
        
        if llm_response.status_code != 200:
            return jsonify({'error': 'Failed to enhance prompt'}), 500
        
        enhanced_prompt = llm_response.json().get('text', prompt)
        
        # Then, generate the image using OpenVINO service
        response = requests.post(
            f"{OPENVINO_URL}/generate-image",
            json={
                'prompt': enhanced_prompt,
                'scene_type': scene_type
            }
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Image generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'Image generation service unavailable', 'details': str(e)}), 503

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
    
    cursor.execute(
        '''
        INSERT INTO vocabulary (user_id, japanese, reading, english, lesson_id)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (user_id, japanese, reading, english, lesson_id)
    )
    
    conn.commit()
    vocab_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': vocab_id, 'status': 'success'})

@app.route('/api/vocabulary/<int:user_id>', methods=['GET'])
def get_vocabulary(user_id):
    lesson_id = request.args.get('lesson_id')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if lesson_id:
        cursor.execute(
            '''
            SELECT id, japanese, reading, english, lesson_id, mastery_level, last_reviewed 
            FROM vocabulary 
            WHERE user_id = ? AND lesson_id = ?
            ''',
            (user_id, lesson_id)
        )
    else:
        cursor.execute(
            '''
            SELECT id, japanese, reading, english, lesson_id, mastery_level, last_reviewed 
            FROM vocabulary 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
    
    vocabulary = [{
        'id': row[0],
        'japanese': row[1],
        'reading': row[2],
        'english': row[3],
        'lesson_id': row[4],
        'mastery_level': row[5],
        'last_reviewed': row[6]
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(vocabulary)

# Initialize the database when the app starts
@app.before_first_request
def before_first_request():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)