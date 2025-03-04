import streamlit as st
import requests
from enum import Enum
import json
from typing import Optional, List, Dict, Any
import logging
import random
import yaml
import os
import sqlite3
import datetime
from manga_ocr import MangaOcr
from PIL import Image
import io
import base64
from streamlit_drawable_canvas import st_canvas
import pathlib

# Setup paths
BASE_DIR = pathlib.Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
VOCAB_DIR = DATA_DIR / "vocabulary"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
for directory in [DATA_DIR, VOCAB_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Database path (adjust as needed)
DB_PATH = BASE_DIR.parent / "listening-speaking" / "langportal.db"

# Setup Custom Logging
logger = logging.getLogger('japanese_writing_app')
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to prevent duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

# Create file handler
log_file = BASE_DIR / "app.log"
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

# Prevent propagation to root logger
logger.propagate = False

# State Management
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class InputMethod(Enum):
    UPLOAD = "upload"
    WEBCAM = "webcam"
    DRAW = "draw"

class EvaluationLevel(Enum):
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"

class PracticeMode(Enum):
    WORDS = "words"
    SENTENCES = "sentences"

class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initializing Japanese Learning App...")
        self.initialize_session_state()
        self.load_prompts()
        self.initialize_database()
        self.load_vocabulary_groups()
        # Initialize MangaOCR
        self.mocr = None  # Will be initialized on demand
        
    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'current_japanese' not in st.session_state:
            st.session_state.current_japanese = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
        if 'input_method' not in st.session_state:
            st.session_state.input_method = InputMethod.UPLOAD
        if 'evaluation_level' not in st.session_state:
            st.session_state.evaluation_level = EvaluationLevel.SENTENCE
        if 'practice_mode' not in st.session_state:
            st.session_state.practice_mode = PracticeMode.SENTENCES
        if 'current_group_id' not in st.session_state:
            st.session_state.current_group_id = 1  # Default to first group
        if 'current_word' not in st.session_state:
            st.session_state.current_word = None
        if 'session_start_time' not in st.session_state:
            st.session_state.session_start_time = datetime.datetime.now()
        if 'correct_count' not in st.session_state:
            st.session_state.correct_count = 0
        if 'total_count' not in st.session_state:
            st.session_state.total_count = 0
    
    def load_prompts(self):
        """Load prompts from YAML file"""
        prompts_file = BASE_DIR / "prompts.yaml"
        try:
            if prompts_file.exists():
                with open(prompts_file, 'r') as file:
                    self.prompts = yaml.safe_load(file)
                logger.debug("Prompts loaded successfully")
            else:
                logger.warning("Prompts file not found, using defaults")
                self.prompts = self.get_default_prompts()
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            st.error(f"Failed to load prompts: {str(e)}")
            self.prompts = self.get_default_prompts()
    
    def get_default_prompts(self):
        """Return default prompts"""
        return {
            "sentence_generation": {
                "system": "You are a Japanese language teacher. Generate a natural Japanese sentence using the provided word. The sentence should use JLPT N5 level grammar and vocabulary only. Respond with the Japanese sentence followed by its English translation in this format: Japanese: [sentence in Japanese] English: [sentence in English]",
                "user": "Generate a natural Japanese sentence using the word: {word}. Use only JLPT N5 level grammar and vocabulary."
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
    
    def initialize_database(self):
        """Initialize database connection and ensure tables exist"""
        try:
            # Check if database file exists
            if not DB_PATH.exists():
                logger.warning(f"Database file not found at {DB_PATH}")
                # Create parent directories if they don't exist
                DB_PATH.parent.mkdir(exist_ok=True, parents=True)
                
                # Create new database with schema
                self.create_database_schema()
            
            # Test connection
            self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            logger.debug("Database connection successful")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            st.error(f"Database error: {str(e)}")
    
    def create_database_schema(self):
        """Create database schema if it doesn't exist"""
        try:
            # Read schema from file
            schema_file = BASE_DIR.parent / "lang-portal" / "schema.sql"
            if schema_file.exists():
                with open(schema_file, 'r') as file:
                    schema_sql = file.read()
                
                # Execute schema SQL
                conn = sqlite3.connect(DB_PATH)
                conn.executescript(schema_sql)
                conn.commit()
                conn.close()
                logger.info("Database schema created successfully")
            else:
                logger.error("Schema file not found")
                st.error("Database schema file not found")
        except Exception as e:
            logger.error(f"Error creating database schema: {e}")
            st.error(f"Error creating database: {str(e)}")
    
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
    
    def load_vocabulary_groups(self):
        """Load vocabulary groups from database"""
        try:
            # Query database for groups
            groups = self.execute_query("SELECT id, name, level FROM word_groups ORDER BY id")
            
            if not groups:
                # Create default groups if none exist
                self.create_default_groups()
                groups = self.execute_query("SELECT id, name, level FROM word_groups ORDER BY id")
            
            self.vocabulary_groups = groups
            logger.debug(f"Loaded {len(groups)} vocabulary groups")
            
            # Load words for current group
            self.load_vocabulary_for_group(st.session_state.current_group_id)
        except Exception as e:
            logger.error(f"Error loading vocabulary groups: {e}")
            st.error(f"Error loading vocabulary: {str(e)}")
            self.vocabulary_groups = []
            self.vocabulary = None
    
    def create_default_groups(self):
        """Create default vocabulary groups"""
        default_groups = [
            ("Basic Greetings", "N5"),
            ("Food and Dining", "N5"),
            ("Travel Phrases", "N5"),
            ("Daily Activities", "N5"),
            ("Numbers and Time", "N5")
        ]
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for name, level in default_groups:
                cursor.execute(
                    "INSERT INTO word_groups (name, level) VALUES (?, ?)",
                    (name, level)
                )
            
            conn.commit()
            conn.close()
            logger.info("Created default vocabulary groups")
        except Exception as e:
            logger.error(f"Error creating default groups: {e}")
    
    def load_vocabulary_for_group(self, group_id):
        """Load vocabulary for a specific group"""
        try:
            # First try to load from JSON file
            json_file = VOCAB_DIR / f"group_{group_id}.json"
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as file:
                    self.vocabulary = json.load(file)
                logger.debug(f"Loaded vocabulary from file for group {group_id}")
            else:
                # If file doesn't exist, load from database
                words = self.execute_query(
                    "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                    (group_id,)
                )
                
                # Get group name
                groups = self.execute_query(
                    "SELECT name FROM word_groups WHERE id = ?",
                    (group_id,)
                )
                group_name = groups[0]['name'] if groups else f"Group {group_id}"
                
                # Format vocabulary
                self.vocabulary = {
                    "group_id": group_id,
                    "group_name": group_name,
                    "words": words
                }
                
                # Save to JSON file for future use
                with open(json_file, 'w', encoding='utf-8') as file:
                    json.dump(self.vocabulary, file, ensure_ascii=False, indent=2)
                
                logger.debug(f"Loaded {len(words)} words from database for group {group_id}")
            
            # Update session state
            st.session_state.current_group_id = group_id
        except Exception as e:
            logger.error(f"Error loading vocabulary for group {group_id}: {e}")
            self.vocabulary = None
    
    def call_ollama(self, prompt, system_prompt=None, model="llama3.2"):
        """Call Ollama API with the given prompt"""
        try:
            logger.debug(f"Calling Ollama with prompt: {prompt[:50]}...")
            
            # Prepare the request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make the API call
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: {response.status_code}"
        except Exception as e:
            logger.error(f"Failed to call Ollama: {e}")
            return f"Error: {str(e)}"
    
    def get_cached_sentence(self, word_id, word_text):
        """Get a cached sentence for a word if available"""
        cache_file = CACHE_DIR / "sentences.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as file:
                    cache = json.load(file)
                
                # Check if word exists in cache
                if str(word_id) in cache:
                    logger.debug(f"Found cached sentence for word {word_text}")
                    return cache[str(word_id)]
            
            return None
        except Exception as e:
            logger.error(f"Error reading sentence cache: {e}")
            return None
    
    def cache_sentence(self, word_id, sentence_data):
        """Cache a generated sentence"""
        cache_file = CACHE_DIR / "sentences.json"
        
        try:
            # Load existing cache or create new one
            cache = {}
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as file:
                    cache = json.load(file)
            
            # Add new sentence to cache
            cache[str(word_id)] = sentence_data
            
            # Save updated cache
            with open(cache_file, 'w', encoding='utf-8') as file:
                json.dump(cache, file, ensure_ascii=False, indent=2)
            
            logger.debug(f"Cached sentence for word ID {word_id}")
        except Exception as e:
            logger.error(f"Error caching sentence: {e}")
    
    def generate_sentence(self, word: dict) -> str:
        """Generate a sentence using Ollama"""
        word_id = word.get('id', 0)
        kanji = word.get('kanji', '')
        english = word.get('english', '')
        
        # Check cache first
        cached_sentence = self.get_cached_sentence(word_id, kanji)
        if cached_sentence:
            # Store the Japanese sentence separately for later use
            st.session_state.current_japanese = cached_sentence.get("japanese", "")
            st.session_state.current_word = word
            return f"Japanese: {cached_sentence.get('japanese', '')}\nEnglish: {cached_sentence.get('english', '')}"
        
        # Format the prompt using the template from prompts.yaml
        system_prompt = self.prompts["sentence_generation"]["system"]
        
        # Add N5 specific instructions
        user_prompt = self.prompts["sentence_generation"]["user"].format(word=kanji)
        user_prompt += "\n\nRemember to use only basic grammar patterns like:\n"
        user_prompt += "- は/が for subject markers\n"
        user_prompt += "- を for direct objects\n"
        user_prompt += "- に/へ for direction/location\n"
        user_prompt += "- で for location of action\n"
        user_prompt += "- simple verb forms (present, past)\n"
        user_prompt += "- basic adjectives\n"
        user_prompt += "Use only common everyday vocabulary appropriate for beginners."
        
        logger.debug(f"Generating sentence for word: {kanji} ({english})")
        
        # Call Ollama API
        response = self.call_ollama(user_prompt, system_prompt)
        
        # Parse the response to extract Japanese and English parts
        lines = response.strip().split('\n')
        japanese = ""
        english = ""
        
        for line in lines:
            if line.startswith("Japanese:"):
                japanese = line.replace("Japanese:", "").strip()
            elif line.startswith("English:"):
                english = line.replace("English:", "").strip()
        
        # If the response doesn't follow the expected format, try to extract what we can
        if not japanese and not english:
            # Assume the first line is Japanese
            if lines:
                japanese = lines[0].strip()
                
                # Try to get a translation
                translation_system = self.prompts["translation"]["system"]
                translation_user = self.prompts["translation"]["user"].format(text=japanese)
                english = self.call_ollama(translation_user, translation_system)
        
        # Store the result
        sentence_data = {
            "japanese": japanese,
            "english": english
        }
        
        # Cache the sentence
        self.cache_sentence(word_id, sentence_data)
        
        result = f"Japanese: {japanese}\nEnglish: {english}"
        logger.debug(f"Generated sentence: {result}")
        
        # Store the Japanese sentence separately for later use
        st.session_state.current_japanese = japanese
        st.session_state.current_word = word
        
        return result
    
    def translate_text(self, text: str) -> str:
        """Translate Japanese text to English using Ollama"""
        # Check cache first
        cache_file = CACHE_DIR / "translations.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as file:
                    cache = json.load(file)
                
                if text in cache:
                    logger.debug(f"Found cached translation for: {text[:20]}...")
                    return cache[text]
        except Exception as e:
            logger.error(f"Error reading translation cache: {e}")
        
        # If not in cache, call Ollama
        system_prompt = self.prompts["translation"]["system"]
        user_prompt = self.prompts["translation"]["user"].format(text=text)
        
        logger.debug(f"Translating text: {text}")
        translation = self.call_ollama(user_prompt, system_prompt)
        logger.debug(f"Translation: {translation}")
        
        # Cache the translation
        try:
            cache = {}
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as file:
                    cache = json.load(file)
            
            cache[text] = translation
            
            with open(cache_file, 'w', encoding='utf-8') as file:
                json.dump(cache, file, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error caching translation: {e}")
        
        return translation
    
    def grade_submission(self, image_data) -> Dict:
        """Process image submission and grade it"""
        try:
            # Initialize MangaOCR if not already done
            if self.mocr is None:
                logger.debug("Initializing MangaOCR...")
                self.mocr = MangaOcr()
                logger.debug("MangaOCR initialized")
            
            # Open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Transcribe the image
            logger.debug("Transcribing image with MangaOCR...")
            transcription = self.mocr(image)
            logger.debug(f"Transcription: {transcription}")
            
            # Get the target sentence (English part)
            current_sentence = st.session_state.current_sentence
            target_english = ""
            for line in current_sentence.split('\n'):
                if line.startswith("English:"):
                    target_english = line.replace("English:", "").strip()
                    break
            
            # Translate the transcription
            translation = self.translate_text(transcription)
            
            # Adjust grading based on evaluation level
            evaluation_level = st.session_state.evaluation_level
            level_specific_prompt = ""
            
            if evaluation_level == EvaluationLevel.CHARACTER:
                level_specific_prompt = "Focus primarily on the correct writing of individual characters (kanji, hiragana, katakana)."
            elif evaluation_level == EvaluationLevel.WORD:
                level_specific_prompt = "Focus primarily on the correct usage and writing of vocabulary words."
            elif evaluation_level == EvaluationLevel.SENTENCE:
                level_specific_prompt = "Focus on the overall sentence structure, grammar, and meaning."
            
            # Grade the submission
            system_prompt = self.prompts["grading"]["system"]
            user_prompt = self.prompts["grading"]["user"].format(
                target_sentence=target_english,
                submission=transcription,
                translation=translation
            )
            
            # Add evaluation level specific instructions
            user_prompt += f"\n\n{level_specific_prompt}"
            
            # Add N5 specific instructions
            user_prompt += "\n\nRemember this is for JLPT N5 level students, so be encouraging and focus on basic grammar and vocabulary issues."
            
            logger.debug("Grading submission...")
            grading_result = self.call_ollama(user_prompt, system_prompt)
            logger.debug(f"Grading result: {grading_result}")
            
            # Parse the grading result
            grade = "C"  # Default grade
            feedback = "Unable to determine feedback."
            
            for line in grading_result.split('\n'):
                if line.startswith("Grade:"):
                    grade = line.replace("Grade:", "").strip()
                elif line.startswith("Feedback:"):
                    feedback = line.replace("Feedback:", "").strip()
            
            # Update statistics
            st.session_state.total_count += 1
            if grade in ['S', 'A']:
                st.session_state.correct_count += 1
                
                # Update word stats in database if we have a current word
                if st.session_state.current_word and 'id' in st.session_state.current_word:
                    self.execute_query(
                        "UPDATE words SET correct_count = correct_count + 1 WHERE id = ?",
                        (st.session_state.current_word['id'],)
                    )
            else:
                # Update word stats for incorrect answers
                if st.session_state.current_word and 'id' in st.session_state.current_word:
                    self.execute_query(
                        "UPDATE words SET wrong_count = wrong_count + 1 WHERE id = ?",
                        (st.session_state.current_word['id'],)
                    )
            
            return {
                "transcription": transcription,
                "translation": translation,
                "grade": grade,
                "feedback": feedback
            }
        except Exception as e:
            logger.error(f"Error in grade_submission: {e}")
            return {
                "transcription": "Error transcribing image",
                "translation": "N/A",
                "grade": "N/A",
                "feedback": f"An error occurred: {str(e)}"
            }
    
    def save_study_session(self):
        """Save the current study session to the database"""
        try:
            # Calculate session duration and accuracy
            end_time = datetime.datetime.now()
            start_time = st.session_state.session_start_time
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            accuracy = 0
            if st.session_state.total_count > 0:
                accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
            
            # Insert session record
            self.execute_query(
                """
                INSERT INTO study_sessions 
                (activity_type, group_id, duration, start_time, end_time, accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    'writing_practice',
                    st.session_state.current_group_id,
                    round(duration_minutes),
                    start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    round(accuracy, 2)
                )
            )
            
            logger.info(f"Saved study session: {duration_minutes:.1f} minutes, {accuracy:.1f}% accuracy")
            
            # Reset session stats
            st.session_state.session_start_time = datetime.datetime.now()
            st.session_state.correct_count = 0
            st.session_state.total_count = 0
        except Exception as e:
            logger.error(f"Error saving study session: {e}")
    
    def render_setup_state(self):
        """Render the setup state UI"""
        logger.debug("Entering render_setup_state")
        st.title("Japanese Writing Practice (JLPT N5)")
        
        # Mode selection (Words/Sentences)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Words", key="words_mode_btn", 
                        type="primary" if st.session_state.practice_mode == PracticeMode.WORDS else "secondary"):
                st.session_state.practice_mode = PracticeMode.WORDS
                st.experimental_rerun()
        
        with col2:
            if st.button("Sentences", key="sentences_mode_btn",
                        type="primary" if st.session_state.practice_mode == PracticeMode.SENTENCES else "secondary"):
                st.session_state.practice_mode = PracticeMode.SENTENCES
                st.experimental_rerun()
        
        st.markdown("---")
        
        # Group selection buttons
        st.subheader("Select Vocabulary Group")
        
        # Create buttons for each vocabulary group
        cols = st.columns(len(self.vocabulary_groups))
        for i, group in enumerate(self.vocabulary_groups):
            with cols[i]:
                if st.button(group['name'], key=f"group_{group['id']}_btn",
                            type="primary" if st.session_state.current_group_id == group['id'] else "secondary"):
                    self.load_vocabulary_for_group(group['id'])
                    st.experimental_rerun()
        
        st.markdown("---")
        
        # Display current group
        current_group = next((g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id), None)
        if current_group:
            st.subheader(f"Current Group: {current_group['name']}")
        
        # Select evaluation level
        st.radio(
            "Select evaluation level:",
            [e.value for e in EvaluationLevel],
            key="evaluation_level_radio",
            on_change=lambda: setattr(st.session_state, 'evaluation_level', 
                                     EvaluationLevel(st.session_state.evaluation_level_radio))
        )
        
        # Generate button
        generate_button = st.button("Generate Practice Item", key="generate_btn")
        
        if generate_button:
            if not self.vocabulary or not self.vocabulary.get('words'):
                st.error("No words found in the selected vocabulary group")
                return
            
            # Pick a random word from vocabulary
            word = random.choice(self.vocabulary['words'])
            logger.debug(f"Selected word: {word.get('english')} - {word.get('kanji')}")
            
            # Generate content based on mode
            with st.spinner("Generating..."):
                if st.session_state.practice_mode == PracticeMode.WORDS:
                    # For word mode, just display the word
                    st.session_state.current_japanese = word.get('kanji', '')
                    st.session_state.current_sentence = f"Japanese: {word.get('kanji', '')}\nEnglish: {word.get('english', '')}"
                    st.session_state.current_word = word
                else:
                    # For sentence mode, generate a sentence
                    st.session_state.current_sentence = self.generate_sentence(word)
            
            st.markdown("### Generated Practice Item")
            st.write(st.session_state.current_sentence)
            
            # Move to practice state
            st.session_state.app_state = AppState.PRACTICE
            st.experimental_rerun()
    
    def render_practice_state(self):
        """Render the practice state UI"""
        st.title("Practice Japanese (JLPT N5)")
        
        # Extract and display the English part of the sentence
        english_sentence = ""
        for line in st.session_state.current_sentence.split('\n'):
            if line.startswith("English:"):
                english_sentence = line.replace("English:", "").strip()
                break
        
        st.write(f"English: {english_sentence}")
        
        # Input method selection
        st.radio(
            "Select input method:",
            [m.value for m in InputMethod],
            key="input_method_radio",
            on_change=lambda: setattr(st.session_state, 'input_method', 
                                     InputMethod(st.session_state.input_method_radio))
        )
        
        # Handle different input methods
        input_method = st.session_state.input_method
        image_data = None
        
        if input_method == InputMethod.UPLOAD:
            uploaded_file = st.file_uploader("Upload your written Japanese", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                image_data = uploaded_file.getvalue()
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)