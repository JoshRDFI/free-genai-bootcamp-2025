import streamlit as st
import requests
import json
import logging
import random
import yaml
import os
import sqlite3
import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
from manga_ocr import MangaOcr
from PIL import Image
import io
import streamlit.components.v1 as components

# Setup paths
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = Path(BASE_DIR, "data")
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = DATA_DIR / "db.sqlite3"

# Setup logging
LOG_FILE = BASE_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)
logger = logging.getLogger('writing_practice')

# State Management
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class WritingPracticeApp:
    def __init__(self):
        logger.info("Initializing Writing Practice App...")
        self.initialize_session_state()
        self.load_prompts()
        self.initialize_database()
        self.load_vocabulary_groups()
        # Initialize MangaOCR on demand
        self.mocr = None
        
    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'current_english' not in st.session_state:
            st.session_state.current_english = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
        if 'current_group_id' not in st.session_state:
            st.session_state.current_group_id = None
        if 'current_word' not in st.session_state:
            st.session_state.current_word = None
        if 'vocabulary' not in st.session_state:
            st.session_state.vocabulary = []
        
        # Check URL parameters for group_id
        query_params = st.query_params
        if 'group_id' in query_params:
            try:
                group_id = int(query_params['group_id'])
                if st.session_state.current_group_id != group_id:
                    st.session_state.current_group_id = group_id
                    # Load vocabulary for this group
                    self.fetch_vocabulary_for_group(group_id)
            except (ValueError, TypeError):
                pass
    
    def load_prompts(self):
        """Load prompts from YAML file"""
        prompts_file = BASE_DIR / "prompts.yaml"
        try:
            if prompts_file.exists():
                with open(prompts_file, 'r') as file:
                    self.prompts = yaml.safe_load(file)
                logger.info("Prompts loaded successfully")
            else:
                logger.warning("Prompts file not found, using defaults")
                self.prompts = {
                    "sentence_generation": {
                        "system": "You are a Japanese language teacher. Generate a simple Japanese sentence using the provided word. The grammar should be scoped to JLPT N5 grammar. Respond with the Japanese sentence followed by its English translation in this format: Japanese: [sentence in Japanese] English: [sentence in English]",
                        "user": "Generate a simple sentence using the following word: {word}. The grammar should be scoped to JLPT N5 grammar. You can use the following vocabulary to construct a simple sentence: simple objects (e.g., book, car, ramen, sushi), simple verbs (to drink, to eat, to meet), simple times (tomorrow, today, yesterday)."
                    },
                    "translation": {
                        "system": "You are a Japanese language translator. Provide a literal, accurate translation of the Japanese text to English. Only respond with the translation, no explanations.",
                        "user": "Translate this Japanese text to English: {text}"
                    },
                    "grading": {
                        "system": "You are a Japanese language teacher grading student writing at the JLPT N5 level. Grade based on: - Accuracy of translation compared to target sentence - Grammar correctness - Writing style and naturalness. Use S/A/B/C grading scale where: S: Perfect or near-perfect, A: Very good with minor issues, B: Good but needs improvement, C: Significant issues to address",
                        "user": "Grade this Japanese writing sample at the JLPT N5 level: Target English sentence: {target_sentence} Student's Japanese: {submission} Literal translation: {translation} Provide your assessment in this format: Grade: [S/A/B/C] Feedback: [Your detailed feedback]"
                    }
                }
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            st.error(f"Failed to load prompts: {str(e)}")
    
    def initialize_database(self):
        """Initialize database connection and check for required tables"""
        try:
            # Check if database file exists
            if not DB_PATH.exists():
                logger.warning(f"Database file not found at {DB_PATH}. Creating new database.")
                # Create data directory if it doesn't exist
                DATA_DIR.mkdir(exist_ok=True, parents=True)
                
                # Create a new database with basic schema
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Create word_groups table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    level TEXT
                )
                ''')
                
                # Create words table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY,
                    kanji TEXT NOT NULL,
                    romaji TEXT,
                    english TEXT NOT NULL,
                    group_id INTEGER,
                    FOREIGN KEY (group_id) REFERENCES word_groups (id)
                )
                ''')
                
                # Create sentences table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    japanese TEXT NOT NULL,
                    english TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES words(id)
                )
                ''')
                
                conn.commit()
                conn.close()
                
                logger.info("Created new database with basic schema")
            
            # Check if required tables exist
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check for word_groups table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='word_groups'")
            word_groups_exists = cursor.fetchone() is not None
            
            # Check for words table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            words_exists = cursor.fetchone() is not None
            
            # Check for sentences table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentences'")
            sentences_exists = cursor.fetchone() is not None
            
            conn.close()
            
            if not word_groups_exists or not words_exists:
                logger.warning("Required tables not found in database. Creating tables.")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                if not word_groups_exists:
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS word_groups (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        level TEXT
                    )
                    ''')
                
                if not words_exists:
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY,
                        kanji TEXT NOT NULL,
                        romaji TEXT,
                        english TEXT NOT NULL,
                        group_id INTEGER,
                        FOREIGN KEY (group_id) REFERENCES word_groups (id)
                    )
                    ''')
                
                if not sentences_exists:
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word_id INTEGER NOT NULL,
                        japanese TEXT NOT NULL,
                        english TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (word_id) REFERENCES words(id)
                    )
                    ''')
                
                conn.commit()
                conn.close()
            
            logger.info("Database connection successful. Required tables found or created.")
            return True
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a database query and return results"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            results = cursor.fetchall()
            conn.commit()
            conn.close()
            
            # Convert to list of dicts
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []
    
    def call_llm(self, prompt, system_prompt=None):
        """Call local LLM with the given prompt"""
        try:
            logger.info(f"Calling LLM with prompt: {prompt[:50]}...")
            
            # Prepare the request payload
            payload = {
                "model": "llama3",  # Use your local model name
                "prompt": prompt,
                "stream": False
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make the API call to local LLM
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return f"Error: {response.status_code}"
        except Exception as e:
            logger.error(f"Failed to call LLM: {e}")
            return f"Error: {str(e)}"
    
    def generate_sentence(self) -> Dict:
        """Generate a sentence using a random word"""
        if not st.session_state.vocabulary:
            logger.warning("No vocabulary available for sentence generation")
            return {"english": "No vocabulary available. Please try again."}
        
        # Pick a random word
        word = random.choice(st.session_state.vocabulary)
        logger.info(f"Selected word for sentence: {word}")
        
        # Format the prompt
        system_prompt = self.prompts["sentence_generation"]["system"]
        user_prompt = self.prompts["sentence_generation"]["user"].format(word=word.get('kanji', ''))
        
        # Call LLM
        response = self.call_llm(user_prompt, system_prompt)
        logger.info(f"LLM response: {response}")
        
        # Parse the response to extract Japanese and English parts
        japanese = ""
        english = ""
        
        for line in response.strip().split('\n'):
            if line.startswith("Japanese:"):
                japanese = line.replace("Japanese:", "").strip()
            elif line.startswith("English:"):
                english = line.replace("English:", "").strip()
        
        # If parsing failed, use the whole response as Japanese and translate it
        if not japanese or not english:
            if response:
                japanese = response.strip()
                # Try to get a translation
                translation_system = self.prompts["translation"]["system"]
                translation_user = self.prompts["translation"]["user"].format(text=japanese)
                english = self.call_llm(translation_user, translation_system)
        
        # Store current word for later reference
        st.session_state.current_word = word
        st.session_state.current_english = english
        
        return {
            "japanese": japanese,
            "english": english
        }
    
    def cache_sentence(self, sentence_data):
        """Cache the generated sentence to both JSON file and database"""
        try:
            # Cache to JSON file
            self.cache_sentence_to_file(sentence_data)
            
            # Cache to database if available
            self.cache_sentence_to_db(sentence_data)
        except Exception as e:
            logger.error(f"Error caching sentence: {e}")
    
    def cache_sentence_to_file(self, sentence_data):
        """Cache the generated sentence to a JSON file"""
        try:
            # Ensure cache directory exists
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            
            # Cache file path
            cache_file = CACHE_DIR / "sentences.json"
            
            # Create a unique key for the sentence
            word_id = st.session_state.current_word.get('id', 0) if st.session_state.current_word else 0
            key = f"{word_id}_{sentence_data.get('japanese', '')[:10]}"
            
            # Load existing cache or create new one
            cache = {}
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as file:
                    try:
                        cache = json.load(file)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in cache file. Creating new cache.")
                        cache = {}
            
            # Add timestamp to the cached data
            sentence_data['timestamp'] = datetime.datetime.now().isoformat()
            
            # Add new sentence to cache
            cache[key] = sentence_data
            
            # Save updated cache
            with open(cache_file, 'w', encoding='utf-8') as file:
                json.dump(cache, file, ensure_ascii=False, indent=2)
            
            logger.info(f"Cached sentence to file with key: {key}")
        except Exception as e:
            logger.error(f"Error caching sentence to file: {e}")
    
    def cache_sentence_to_db(self, sentence_data):
        """Cache the generated sentence to the database if available"""
        try:
            # Check if database is ready
            if not DB_PATH.exists():
                logger.warning("Database file not found. Cannot cache sentence to database.")
                return
            
            # Check if current_word is available
            if not st.session_state.current_word or 'id' not in st.session_state.current_word:
                logger.warning("No current word available. Cannot cache sentence to database.")
                return
            
            word_id = st.session_state.current_word.get('id', 0)
            japanese = sentence_data.get('japanese', '')
            english = sentence_data.get('english', '')
            
            # Check if we have a sentences table
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if sentences table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentences'")
            if not cursor.fetchone():
                # Create sentences table if it doesn't exist
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    japanese TEXT NOT NULL,
                    english TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES words(id)
                )
                """)
                conn.commit()
            
            # Insert the sentence
            cursor.execute(
                "INSERT OR IGNORE INTO sentences (word_id, japanese, english) VALUES (?, ?, ?)",
                (word_id, japanese, english)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cached sentence to database for word ID: {word_id}")
        except Exception as e:
            logger.error(f"Error caching sentence to database: {e}")
    
    def get_cached_sentence(self, word_id):
        """Try to get a cached sentence for the given word ID"""
        try:
            # First try to get from database
            sentence = self.get_cached_sentence_from_db(word_id)
            if sentence:
                return sentence
            
            # If not in database, try to get from file
            return self.get_cached_sentence_from_file(word_id)
        except Exception as e:
            logger.error(f"Error getting cached sentence: {e}")
            return None
    
    def get_cached_sentence_from_db(self, word_id):
        """Try to get a cached sentence from the database"""
        try:
            # Check if database is ready
            if not DB_PATH.exists():
                return None
            
            # Check if sentences table exists
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentences'")
            if not cursor.fetchone():
                conn.close()
                return None
            
            # Get a random sentence for this word
            cursor.execute(
                "SELECT japanese, english FROM sentences WHERE word_id = ? ORDER BY RANDOM() LIMIT 1",
                (word_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                logger.info(f"Found cached sentence in database for word ID: {word_id}")
                return {
                    "japanese": result[0],
                    "english": result[1]
                }
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached sentence from database: {e}")
            return None
    
    def get_cached_sentence_from_file(self, word_id):
        """Try to get a cached sentence from the JSON file"""
        try:
            cache_file = CACHE_DIR / "sentences.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as file:
                try:
                    cache = json.load(file)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in cache file.")
                    return None
            
            # Look for sentences with this word_id
            matching_sentences = []
            for key, sentence in cache.items():
                if key.startswith(f"{word_id}_"):
                    matching_sentences.append(sentence)
            
            if matching_sentences:
                # Return a random matching sentence
                sentence = random.choice(matching_sentences)
                logger.info(f"Found cached sentence in file for word ID: {word_id}")
                return sentence
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached sentence from file: {e}")
            return None
    
    def load_vocabulary_groups(self):
        """Load vocabulary groups from database"""
        try:
            # Check if database is ready
            if not DB_PATH.exists():
                logger.warning("Database file not found. Cannot load vocabulary groups.")
                self.vocabulary_groups = []
                return False
            
            # Query database for groups
            groups = self.execute_query("SELECT id, name, level FROM word_groups ORDER BY id")
            
            if not groups:
                # Try to create default groups if none exist
                if self.create_default_groups():
                    groups = self.execute_query("SELECT id, name, level FROM word_groups ORDER BY id")
            
            self.vocabulary_groups = groups if groups else []
            logger.info(f"Loaded {len(self.vocabulary_groups)} vocabulary groups")
            
            # Load words for current group if one is selected
            if st.session_state.current_group_id:
                self.fetch_vocabulary_for_group(st.session_state.current_group_id)
                
            return len(self.vocabulary_groups) > 0
        except Exception as e:
            logger.error(f"Error loading vocabulary groups: {e}")
            self.vocabulary_groups = []
            return False
    
    def create_default_groups(self):
        """Create default vocabulary groups if they don't exist"""
        default_groups = [
            (1, "Basic Greetings", "N5"),
            (2, "Food & Dining", "N5"),
            (3, "Travel Phrases", "N5"),
            (4, "Daily Activities", "N5"),
            (5, "Numbers & Time", "N5")
        ]
        
        try:
            # Check if database exists
            if not DB_PATH.exists():
                logger.warning("Database file not found. Cannot create default groups.")
                return False
                
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if word_groups table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='word_groups'")
            if not cursor.fetchone():
                logger.warning("word_groups table doesn't exist. Creating it.")
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    level TEXT
                )
                ''')
            
            # Check if words table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            if not cursor.fetchone():
                logger.warning("words table doesn't exist. Creating it.")
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY,
                    kanji TEXT NOT NULL,
                    romaji TEXT,
                    english TEXT NOT NULL,
                    group_id INTEGER,
                    FOREIGN KEY (group_id) REFERENCES word_groups (id)
                )
                ''')
            
            # Insert default groups with specific IDs
            groups_created = False
            for group_id, name, level in default_groups:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO word_groups (id, name, level) VALUES (?, ?, ?)",
                        (group_id, name, level)
                    )
                    if cursor.rowcount > 0:
                        groups_created = True
                        # Create sample words for this group if it was newly created
                        self.create_sample_words_for_group_with_conn(conn, group_id)
                except sqlite3.Error as e:
                    logger.error(f"Error inserting group {name}: {e}")
            
            conn.commit()
            conn.close()
            
            if groups_created:
                logger.info("Created default vocabulary groups and sample words")
            else:
                logger.info("Default vocabulary groups already exist")
                
            return True
        except Exception as e:
            logger.error(f"Error creating default groups: {e}")
            return False
    
    def create_sample_words_for_group_with_conn(self, conn, group_id):
        """Create sample words for a specific group using the provided connection"""
        # Different sample words based on group ID
        sample_words_by_group = {
            1: [  # Basic Greetings
                ("こんにちは", "konnichiwa", "hello"),
                ("おはよう", "ohayou", "good morning"),
                ("こんばんは", "konbanwa", "good evening"),
                ("さようなら", "sayounara", "goodbye"),
                ("ありがとう", "arigatou", "thank you")
            ],
            2: [  # Food & Dining
                ("ごはん", "gohan", "rice/meal"),
                ("水", "mizu", "water"),
                ("お茶", "ocha", "tea"),
                ("肉", "niku", "meat"),
                ("野菜", "yasai", "vegetables")
            ],
            3: [  # Travel Phrases
                ("駅", "eki", "station"),
                ("バス", "basu", "bus"),
                ("ホテル", "hoteru", "hotel"),
                ("いくら", "ikura", "how much"),
                ("どこ", "doko", "where")
            ],
            4: [  # Daily Activities
                ("食べる", "taberu", "to eat"),
                ("飲む", "nomu", "to drink"),
                ("見る", "miru", "to see"),
                ("行く", "iku", "to go"),
                ("寝る", "neru", "to sleep")
            ],
            5: [  # Numbers & Time
                ("一", "ichi", "one"),
                ("二", "ni", "two"),
                ("三", "san", "three"),
                ("今日", "kyou", "today"),
                ("明日", "ashita", "tomorrow")
            ]
        }
        
        # Default to basic greetings if group ID not found
        sample_words = sample_words_by_group.get(group_id, sample_words_by_group[1])
        
        try:
            cursor = conn.cursor()
            
            for kanji, romaji, english in sample_words:
                cursor.execute(
                    "INSERT OR IGNORE INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
                    (kanji, romaji, english, group_id)
                )
            
            logger.info(f"Created sample words for group {group_id}")
        except Exception as e:
            logger.error(f"Error creating sample words for group {group_id}: {e}")
    
    def fetch_vocabulary_for_group(self, group_id):
        """Fetch vocabulary for a specific group"""
        try:
            logger.info(f"Fetching vocabulary for group {group_id}...")
            
            # First try to fetch from API
            api_success = False
            try:
                logger.info(f"Attempting to fetch from API at http://localhost:5000/api/groups/{group_id}/raw")
                response = requests.get(f"http://localhost:5000/api/groups/{group_id}/raw", timeout=5)
                if response.status_code == 200:
                    vocabulary = response.json()
                    logger.info(f"Successfully fetched {len(vocabulary)} words from API")
                    st.session_state.vocabulary = vocabulary
                    st.session_state.current_group_id = group_id
                    api_success = True
                else:
                    logger.warning(f"API returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Failed to fetch from API: {e}. Falling back to database.")
            
            # If API fails, fall back to database
            if not api_success:
                logger.info(f"Fetching vocabulary from database for group {group_id}")
                words = self.execute_query(
                    "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                    (group_id,)
                )
                
                if words:
                    logger.info(f"Loaded {len(words)} words from database for group {group_id}")
                    st.session_state.vocabulary = words
                    st.session_state.current_group_id = group_id
                else:
                    # If no words found, create some sample words for this group
                    logger.warning(f"No words found in database for group {group_id}. Creating sample words.")
                    conn = sqlite3.connect(DB_PATH)
                    self.create_sample_words_for_group_with_conn(conn, group_id)
                    conn.commit()
                    conn.close()
                    
                    # Fetch the newly created words
                    words = self.execute_query(
                        "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                        (group_id,)
                    )
                    
                    if words:
                        logger.info(f"Created and loaded {len(words)} sample words for group {group_id}")
                        st.session_state.vocabulary = words
                        st.session_state.current_group_id = group_id
                    else:
                        logger.error(f"Failed to create sample words for group {group_id}")
                        st.session_state.vocabulary = []
                        # Still set the group ID so the UI shows the selection
                        st.session_state.current_group_id = group_id
            
            # Log the current state for debugging
            logger.info(f"Current group ID: {st.session_state.current_group_id}")
            logger.info(f"Vocabulary count: {len(st.session_state.vocabulary)}")
            
        except Exception as e:
            logger.error(f"Error fetching vocabulary for group {group_id}: {e}")
            # Set empty vocabulary but still set the group ID
            st.session_state.vocabulary = []
            st.session_state.current_group_id = group_id

    def process_image(self, image_data) -> Dict:
        """Process image with MangaOCR and grade the submission"""
        try:
            # Initialize MangaOCR if not already done
            if self.mocr is None:
                logger.info("Initializing MangaOCR...")
                self.mocr = MangaOcr()
                logger.info("MangaOCR initialized")
            
            # Open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Transcribe the image
            logger.info("Transcribing image with MangaOCR...")
            transcription = self.mocr(image)
            logger.info(f"Transcription: {transcription}")
            
            # Translate the transcription
            translation_system = self.prompts["translation"]["system"]
            translation_user = self.prompts["translation"]["user"].format(text=transcription)
            translation = self.call_llm(translation_user, translation_system)
            logger.info(f"Translation: {translation}")
            
            # Grade the submission
            target_sentence = st.session_state.current_english
            
            grading_system = self.prompts["grading"]["system"]
            grading_user = self.prompts["grading"]["user"].format(
                target_sentence=target_sentence,
                submission=transcription,
                translation=translation
            )
            
            grading_result = self.call_llm(grading_user, grading_system)
            logger.info(f"Grading result: {grading_result}")
            
            # Parse the grading result
            grade = "C"  # Default grade
            feedback = "Unable to determine feedback."
            
            for line in grading_result.split('\n'):
                if line.startswith("Grade:"):
                    grade = line.replace("Grade:", "").strip()
                elif line.startswith("Feedback:"):
                    feedback = line.replace("Feedback:", "").strip()
            
            # Return the results
            return {
                "transcription": transcription,
                "translation": translation,
                "grade": grade,
                "feedback": feedback
            }
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "transcription": "Error processing image",
                "translation": "Error",
                "grade": "N/A",
                "feedback": f"An error occurred: {str(e)}"
            }
            
    def render_setup_state(self):
        """Render the setup state UI"""
        st.title("Japanese Writing Practice")
        st.write("Welcome to the Japanese Writing Practice app. Select a vocabulary category and click 'Generate Sentence' to begin.")
        
        # Check if database is ready
        db_ready = DB_PATH.exists()
        if not db_ready:
            st.warning("Database not found. Please ensure the main system setup has been completed.")
            return
        
        # Load vocabulary groups if not already loaded
        if not hasattr(self, 'vocabulary_groups') or not self.vocabulary_groups:
            groups_loaded = self.load_vocabulary_groups()
            if not groups_loaded:
                st.warning("Could not load vocabulary categories. Please ensure the main system setup has been completed.")
                return
        
        # Category selection using a dropdown instead of buttons
        st.subheader("Select Vocabulary Category")
        
        if self.vocabulary_groups and len(self.vocabulary_groups) > 0:
            # Create a list of group names and IDs for the dropdown
            group_options = {group['name']: group['id'] for group in self.vocabulary_groups}
            
            # Get the current selection (if any)
            current_group_name = None
            if st.session_state.current_group_id:
                for group in self.vocabulary_groups:
                    if group['id'] == st.session_state.current_group_id:
                        current_group_name = group['name']
                        break
            
            # Create the dropdown
            selected_group = st.selectbox(
                "Choose a category:",
                options=list(group_options.keys()),
                index=list(group_options.keys()).index(current_group_name) if current_group_name else 0
            )
            
            # Handle selection change
            selected_group_id = group_options[selected_group]
            if selected_group_id != st.session_state.current_group_id:
                st.session_state.current_group_id = selected_group_id
                self.fetch_vocabulary_for_group(selected_group_id)
                st.query_params.group_id = selected_group_id
        else:
            st.info("No vocabulary categories found. The system may still be initializing.")
            return
        
        # Display current category info
        if st.session_state.current_group_id:
            current_group = next((g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id), None)
            if current_group:
                st.info(f"Selected category: {current_group['name']} (JLPT Level: {current_group.get('level', 'N/A')})")
                
                # Show vocabulary count
                vocab_count = len(st.session_state.vocabulary)
                st.write(f"This category contains {vocab_count} vocabulary items.")
        
        # Generate button (only enabled if a category is selected)
        if st.session_state.current_group_id:
            if st.button("Generate Sentence", key="generate_btn"):
                with st.spinner("Generating sentence..."):
                    try:
                        sentence_data = self.generate_sentence()
                        
                        # Cache the generated sentence
                        self.cache_sentence(sentence_data)
                        
                        st.session_state.current_sentence = sentence_data
                        st.session_state.app_state = AppState.PRACTICE
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error generating sentence: {e}")
                        st.error("Failed to generate sentence. Please try again.")
        else:
            st.info("Please select a vocabulary category first.")
    
    def render_practice_state(self):
        """Render the practice state UI"""
        st.title("Practice Writing")
        
        # Display the English sentence to translate
        st.subheader("Write this sentence in Japanese:")
        st.write(st.session_state.current_english)
        
        # Three input methods
        input_method = st.radio(
            "Choose input method:",
            ["Upload Image", "Draw (Canvas)", "Take Photo"]
        )
        
        if input_method == "Upload Image":
            # File uploader for the written Japanese
            uploaded_file = st.file_uploader("Upload your written Japanese", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file is not None:
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
                
                if st.button("Submit for Review"):
                    with st.spinner("Processing submission..."):
                        # Process the image
                        image_data = uploaded_file.getvalue()
                        review_data = self.process_image(image_data)
                        
                        # Store review data and change state
                        st.session_state.review_data = review_data
                        st.session_state.app_state = AppState.REVIEW
                        st.rerun()
        
        elif input_method == "Draw (Canvas)":
            # Create a canvas for drawing
            canvas_result = st.empty()
            
            # Use HTML/JS to create a simple drawing canvas
            canvas_html = """
            <canvas id="drawingCanvas" width="400" height="200" style="border:1px solid #000000;"></canvas>
            <br>
            <button id="clearButton">Clear Canvas</button>
            <button id="saveButton">Save Drawing</button>
            
            <script>
            const canvas = document.getElementById('drawingCanvas');
            const ctx = canvas.getContext('2d');
            let isDrawing = false;
            
            // Set up the canvas
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.strokeStyle = 'black';
            
            // Event listeners for drawing
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
            canvas.addEventListener('mouseout', stopDrawing);
            
            // Touch support
            canvas.addEventListener('touchstart', handleTouch);
            canvas.addEventListener('touchmove', handleTouch);
            canvas.addEventListener('touchend', stopDrawing);
            
            // Clear button
            document.getElementById('clearButton').addEventListener('click', clearCanvas);
            
            // Save button
            document.getElementById('saveButton').addEventListener('click', saveDrawing);
            
            function startDrawing(e) {
                isDrawing = true;
                draw(e);
            }
            
            function draw(e) {
                if (!isDrawing) return;
                
                // Get mouse position
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                ctx.lineTo(x, y);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(x, y);
            }
            
            function stopDrawing() {
                isDrawing = false;
                ctx.beginPath();
            }
            
            function handleTouch(e) {
                e.preventDefault();
                if (e.type === 'touchstart') {
                    isDrawing = true;
                }
                
                if (isDrawing) {
                    const rect = canvas.getBoundingClientRect();
                    const touch = e.touches[0];
                    const x = touch.clientX - rect.left;
                    const y = touch.clientY - rect.top;
                    
                    if (e.type === 'touchstart') {
                        ctx.beginPath();
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                        ctx.stroke();
                    }
                }
            }
            
            function clearCanvas() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
            
            function saveDrawing() {
                const dataURL = canvas.toDataURL('image/png');
                
                // Create a link to download the image
                const link = document.createElement('a');
                link.href = dataURL;
                link.download = 'japanese-writing.png';
                link.click();
                
                // Also send to Streamlit
                if (window.parent.postMessage) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: dataURL
                    }, '*');
                }
            }
            </script>
            """
            
            components.html(canvas_html, height=300)
            
            st.info("After drawing, click 'Save Drawing' to download your image, then upload it using the 'Upload Image' option.")
        
        elif input_method == "Take Photo":
            st.info("Take a photo of your handwritten Japanese and upload it using the 'Upload Image' option.")
            
            # Add a camera input if the browser supports it
            camera_html = """
            <div>
                <video id="video" width="400" height="300" autoplay></video>
                <br>
                <button id="captureButton">Capture Photo</button>
                <br><br>
                <canvas id="canvas" width="400" height="300" style="display:none;"></canvas>
                <br>
                <img id="photo" width="400" height="300" style="display:none;">
            </div>
            
            <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const photo = document.getElementById('photo');
            const captureButton = document.getElementById('captureButton');
            const ctx = canvas.getContext('2d');
            
            // Access the camera
            async function startCamera() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = stream;
                } catch (err) {
                    console.error("Error accessing camera: ", err);
                    document.body.innerHTML += "<p>Error accessing camera. Please use the 'Upload Image' option instead.</p>";
                }
            }
            
            // Capture photo
            captureButton.addEventListener('click', function() {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const dataURL = canvas.toDataURL('image/png');
                photo.src = dataURL;
                photo.style.display = 'block';
                
                // Create a link to download the image
                const link = document.createElement('a');
                link.href = dataURL;
                link.download = 'japanese-writing.png';
                link.click();
                
                // Also send to Streamlit
                if (window.parent.postMessage) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: dataURL
                    }, '*');
                }
            });
            
            // Start the camera when the page loads
            startCamera();
            </script>
            """
            
            components.html(camera_html, height=400)
            
            st.info("After capturing a photo, it will be downloaded automatically. Then upload it using the 'Upload Image' option.")
    
    def render_review_state(self):
        """Render the review state UI"""
        st.title("Review")
        
        # Display the original English sentence
        st.subheader("Original English Sentence:")
        st.write(st.session_state.current_english)
        
        # Display the review data
        review_data = st.session_state.review_data
        
        st.subheader("Your Submission:")
        st.write(f"**Transcription:** {review_data['transcription']}")
        st.write(f"**Translation:** {review_data['translation']}")
        
        st.subheader("Grading:")
        st.write(f"**Grade:** {review_data['grade']}")
        st.write(f"**Feedback:** {review_data['feedback']}")
        
        # Next question button
        if st.button("Next Question"):
            # Reset state and generate new sentence
            st.session_state.app_state = AppState.SETUP
            st.rerun()
    
    def run(self):
        """Run the application based on current state"""
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

# Main entry point
if __name__ == "__main__":
    app = WritingPracticeApp()
    app.run()