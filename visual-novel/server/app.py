import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import requests

app = Flask(__name__)
CORS(app)

# Configuration
# All external services should be accessed through the opea-docker API endpoints
OPEA_API_BASE_URL = os.environ.get('OPEA_API_BASE_URL', 'http://opea-api-gateway:8000')

# Service-specific endpoints
LLM_TEXT_URL = f"{OPEA_API_BASE_URL}/llm/text"
TTS_URL = f"{OPEA_API_BASE_URL}/tts"
ASR_URL = f"{OPEA_API_BASE_URL}/asr"
LLM_VISION_URL = f"{OPEA_API_BASE_URL}/llm/vision"
EMBEDDINGS_URL = f"{OPEA_API_BASE_URL}/embeddings"
IMAGE_GEN_URL = f"{OPEA_API_BASE_URL}/image/generate"
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
    
    try:
        response = requests.post(
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': f"Generate a Japanese conversation with the following context: {context}\n\n"
                         f"Characters: {', '.join(characters)}\n\n"
                         f"Grammar points to include: {', '.join(grammar_points)}\n\n"
                         f"Vocabulary to include: {', '.join(vocabulary)}\n\n"
                         f"Number of exchanges: {num_exchanges}\n\n"
                         f"Include English translations: {include_translations}\n\n"
                         f"Format the response as a JSON array of dialogue exchanges.",
                'max_tokens': 2000,
                'temperature': 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Process the LLM response to ensure it's in the correct format
            conversation = result.get('text', '')
            try:
                # Try to parse the response as JSON
                conversation_data = json.loads(conversation)
                return jsonify({'conversation': conversation_data})
            except json.JSONDecodeError:
                # If parsing fails, return the raw text
                return jsonify({'error': 'Failed to parse conversation', 'raw_response': conversation}), 500
        else:
            return jsonify({'error': 'Conversation generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'Conversation generation service unavailable', 'details': str(e)}), 503

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
    
    try:
        response = requests.post(
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': f"Generate a complete JLPT N5 Japanese lesson on the topic: {topic}\n\n"
                         f"Grammar points to include: {', '.join(grammar_points)}\n\n"
                         f"Vocabulary focus: {', '.join(vocabulary_focus)}\n\n"
                         f"Lesson number: {lesson_number}\n\n"
                         f"Scene setting: {scene_setting}\n\n"
                         f"Format the response as a JSON object with the following structure:\n"
                         f"{{\n"
                         f"  'metadata': {{\n"
                         f"    'title': 'Lesson title',\n"
                         f"    'objectives': ['objective1', 'objective2', ...]\n"
                         f"  }},\n"
                         f"  'vocabulary': [\n"
                         f"    {{'japanese': '日本語', 'reading': 'にほんご', 'english': 'Japanese language'}},\n"
                         f"    ...\n"
                         f"  ],\n"
                         f"  'grammar_points': [\n"
                         f"    {{'pattern': 'Pattern', 'explanation': 'Explanation', 'examples': ['Example1', 'Example2']}},\n"
                         f"    ...\n"
                         f"  ],\n"
                         f"  'dialogue_script': [\n"
                         f"    {{'speaker': 'Character name', 'japanese': 'Japanese text', 'english': 'English translation'}},\n"
                         f"    ...\n"
                         f"  ],\n"
                         f"  'exercises': [\n"
                         f"    {{'question': 'Question', 'options': ['Option1', 'Option2', ...], 'correct_answer': 'Correct option'}},\n"
                         f"    ...\n"
                         f"  ],\n"
                         f"  'cultural_note': 'Cultural information related to the lesson'\n"
                         f"}}",
                'max_tokens': 4000,
                'temperature': 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Process the LLM response to ensure it's in the correct format
            lesson_text = result.get('text', '')
            try:
                # Try to parse the response as JSON
                lesson_data = json.loads(lesson_text)
                return jsonify({'lesson': lesson_data})
            except json.JSONDecodeError:
                # If parsing fails, return the raw text
                return jsonify({'error': 'Failed to parse lesson', 'raw_response': lesson_text}), 500
        else:
            return jsonify({'error': 'Lesson generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'Lesson generation service unavailable', 'details': str(e)}), 503

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

# Initialize database when the app starts
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
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
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': prompt,
                'max_tokens': 2000,
                'temperature': 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Try to extract and parse the JSON from the response
            try:
                # The LLM might include markdown code blocks or extra text
                text = result.get('text', '')
                
                # Try to extract JSON if it's wrapped in code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
                
                if json_match:
                    conversation_json = json.loads(json_match.group(1))
                else:
                    # Try parsing the whole response as JSON
                    conversation_json = json.loads(text)
                
                return jsonify(conversation_json)
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, return the raw text
                return jsonify({
                    'error': 'Failed to parse LLM response as JSON',
                    'raw_response': text
                }), 422
        else:
            return jsonify({'error': 'Conversation generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'LLM service unavailable', 'details': str(e)}), 503

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
        
        # Then, generate the image using the opea-docker image generation service
        response = requests.post(
            f"{IMAGE_GEN_URL}",
            json={
                'prompt': enhanced_prompt,
                'scene_type': scene_type,
                'style': 'anime',
                'width': 512,
                'height': 512
            }
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Image generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'Image generation service unavailable', 'details': str(e)}), 503

@app.route('/api/generate-lesson', methods=['POST'])
def generate_lesson():
    data = request.json
    topic = data.get('topic')
    grammar_points = data.get('grammar_points', [])
    vocabulary_focus = data.get('vocabulary_focus', [])
    lesson_number = data.get('lesson_number', 1)
    scene_setting = data.get('scene_setting', 'classroom')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # Construct a detailed prompt for the LLM
    prompt = f"""
    Create a complete JLPT N5 level Japanese lesson for a visual novel game based on the following:
    
    TOPIC: {topic}
    LESSON NUMBER: {lesson_number}
    SCENE SETTING: {scene_setting}
    GRAMMAR POINTS TO TEACH: {', '.join(grammar_points)}
    VOCABULARY FOCUS: {', '.join(vocabulary_focus)}
    
    INSTRUCTIONS:
    - Create a structured lesson with introduction, explanation, practice, and review sections
    - Use only JLPT N5 level grammar and vocabulary
    - Include at least 10 vocabulary words with readings and translations
    - Include clear explanations of the grammar points
    - Include practice dialogues that use the grammar and vocabulary
    - Include at least one interactive choice for the player
    - Format the output as a JSON structure with the following sections:
      - metadata (title, level, objectives)
      - vocabulary (list of words with readings and translations)
      - grammar_points (explanations and examples)
      - dialogue_script (conversation exchanges with speaker, text, and translations)
      - practice_exercises (interactive exercises with questions and answers)
      - review_summary (key points to remember)
    
    Example format:
    ```json
    {{
      "metadata": {{
        "title": "Introducing Yourself",
        "level": "JLPT N5",
        "objectives": ["Learn basic greetings", "Practice self-introduction"]
      }},
      "vocabulary": [
        {{
          "japanese": "こんにちは",
          "reading": "こんにちは",
          "english": "Hello"
        }}
      ],
      "grammar_points": [
        {{
          "point": "です/ます form",
          "explanation": "Polite form of verbs and adjectives",
          "examples": [
            {{
              "japanese": "私は学生です。",
              "reading": "わたしはがくせいです。",
              "english": "I am a student."
            }}
          ]
        }}
      ],
      "dialogue_script": [
        {{
          "speaker": "Sensei",
          "japanese": "おはようございます。",
          "english": "Good morning."
        }},
        {{
          "speaker": "Student",
          "japanese": "おはようございます。",
          "english": "Good morning."
        }}
      ],
      "practice_exercises": [
        {{
          "question": "How do you say 'My name is [name]' in Japanese?",
          "options": [
            "私の名前は[name]です。",
            "私は[name]と申します。",
            "[name]と言います。"
          ],
          "correct_answer": 0,
          "explanation": "All are correct, but the first is the most common for beginners."
        }}
      ],
      "review_summary": [
        "Today we learned basic greetings in Japanese.",
        "We practiced introducing ourselves using the です form."
      ]
    }}
    ```
    
    Generate only the JSON response without any additional text.
    """
    
    try:
        response = requests.post(
            f"{LLM_TEXT_URL}/generate",
            json={
                'prompt': prompt,
                'max_tokens': 4000,
                'temperature': 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Try to extract and parse the JSON from the response
            try:
                # The LLM might include markdown code blocks or extra text
                text = result.get('text', '')
                
                # Try to extract JSON if it's wrapped in code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
                
                if json_match:
                    lesson_json = json.loads(json_match.group(1))
                else:
                    # Try parsing the whole response as JSON
                    lesson_json = json.loads(text)
                
                return jsonify(lesson_json)
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, return the raw text
                return jsonify({
                    'error': 'Failed to parse LLM response as JSON',
                    'raw_response': text
                }), 422
        else:
            return jsonify({'error': 'Lesson generation error', 'details': response.text}), 500
    except requests.RequestException as e:
        return jsonify({'error': 'LLM service unavailable', 'details': str(e)}), 503

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