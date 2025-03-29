# app.py
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
from flask import Flask, jsonify
import threading
import numpy as np
from streamlit_drawable_canvas import st_canvas

# Setup paths
BASE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = DATA_DIR / "db.sqlite3"

# Setup logging
LOG_FILE = BASE_DIR / "app.log"
# Modify the logging configuration (near top of app.py)
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ],
)
# Add these lines after logger configuration
logging.getLogger('watchdog').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Enable debug mode in config
DEBUG = os.environ.get('STREAMLIT_DEBUG', 'false').lower() == 'true'

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
        self.mocr = None  # Initialize MangaOCR on demand

        try:
            response = requests.get("http://localhost:5000/api/groups/1/raw", timeout=2)
            if response.status_code != 200:
                self.start_api_server()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self.start_api_server()

    def start_api_server(self):
        """Start the API server on port 5000"""
        app = Flask(__name__)

        @app.route('/api/groups/<int:group_id>/raw')
        def get_group_words(group_id):
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                        (group_id,)
                    )
                    columns = [col[0] for col in cursor.description]
                    words = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return jsonify(words)
            except Exception as e:
                logger.error(f"API error: {e}")
                return jsonify({"error": str(e)}), 500

        def run_flask():
            app.run(port=5000, use_reloader=False)

        threading.Thread(target=run_flask, daemon=True).start()
        logger.info("API server started on port 5000")

    def set_background(self, image_name: str):
        """Set background image for current state"""
        bg_path = BASE_DIR / "images" / image_name
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url('{bg_path}') no-repeat center center fixed;
                background-size: cover;
            }}
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                padding: 2rem;
                margin: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    def initialize_session_state(self):
        """Initialize session state variables"""
        initial_states = {
            'app_state': AppState.SETUP,
            'current_sentence': "",
            'current_english': "",
            'review_data': None,
            'current_group_id': None,
            'current_word': None,
            'vocabulary': [],
            'debug_mode': DEBUG,
            'last_action': None,
            'error_log': []
        }

        for key, default_value in initial_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        logger.debug(f"Current app state: {st.session_state.app_state}")

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
                        "system": "You are a Japanese language teacher...",
                        "user": "Generate a simple sentence using..."
                    }
                }
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            self.prompts = {}

    def initialize_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.cursor = self.conn.cursor()
            logger.info(f"Database connection established at {DB_PATH}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS word_groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    level TEXT NOT NULL
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY,
                    kanji TEXT NOT NULL,
                    romaji TEXT NOT NULL,
                    english TEXT NOT NULL,
                    group_id INTEGER,
                    FOREIGN KEY(group_id) REFERENCES word_groups(id)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentences (
                    id INTEGER PRIMARY KEY,
                    japanese TEXT NOT NULL,
                    english TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL
                )
            """)
            self.conn.commit()

            self.cursor.execute("SELECT COUNT(*) FROM word_groups")
            if self.cursor.fetchone()[0] == 0:
                self.load_sample_data()

        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            st.error("Failed to connect to database")

    def load_sample_data(self):
        """Load sample data if database is empty"""
        sample_groups = [("Basic Starter Words", "N5")]
        sample_words = [
            ("こんにちは", "konnichiwa", "Hello", 1),
            ("ありがとう", "arigatou", "Thank you", 1),
            ("さようなら", "sayounara", "Goodbye", 1)
        ]
        try:
            self.cursor.executemany(
                "INSERT INTO word_groups (name, level) VALUES (?, ?)",
                sample_groups
            )
            self.cursor.executemany(
                "INSERT INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
                sample_words
            )
            self.conn.commit()
            logger.info("Sample data loaded successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to load sample data: {e}")

    def load_vocabulary_groups(self):
        """Load vocabulary groups from database"""
        try:
            self.vocabulary_groups = self.execute_query(
                "SELECT id, name, level FROM word_groups ORDER BY level"
            )
            logger.info(f"Loaded {len(self.vocabulary_groups)} vocabulary groups")
            return True
        except Exception as e:
            logger.error(f"Error loading vocabulary groups: {e}")
            return False

    def execute_query(self, query, params=()):
        """Execute a database query"""
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                columns = [col[0] for col in self.cursor.description]
                return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False

    def fetch_vocabulary_for_group(self, group_id):
        """Fetch vocabulary for a specific group"""
        try:
            response = requests.get(f"http://localhost:5000/api/groups/{group_id}/raw", timeout=5)
            if response.status_code == 200:
                st.session_state.vocabulary = response.json()
                logger.info(f"Loaded {len(st.session_state.vocabulary)} words from API for group {group_id}")
                return
        except Exception as api_error:
            logger.warning(f"API fetch failed: {api_error}. Falling back to database.")

        try:
            st.session_state.vocabulary = self.execute_query(
                "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                (group_id,)
            )
            logger.info(f"Loaded {len(st.session_state.vocabulary)} words from database for group {group_id}")
        except Exception as db_error:
            logger.error(f"Database fetch failed: {db_error}")
            st.error("Failed to load vocabulary")

    def render_setup_state(self):
        """Render the setup state UI"""
        self.set_background("1240417.png")
        st.title("Japanese Writing Practice")
        st.write("Welcome to the Japanese Writing Practice app. Select a category to begin.")

        if not self.vocabulary_groups:
            st.warning("No vocabulary categories found. The system may still be initializing.")
            return

        cols = st.columns(3)
        for idx, group in enumerate(self.vocabulary_groups):
            with cols[idx % 3]:
                if st.button(
                    f"{group['name']}\n({group['level']})",
                    key=f"group_{group['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_group_id = group['id']
                    self.fetch_vocabulary_for_group(group['id'])

        if st.session_state.current_group_id:
            selected_name = next(
                (g['name'] for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id),
                'Unknown Group'
            )
            st.markdown("---")
            st.info(f"Selected Category: **{selected_name}**")

            if st.button(
                "Generate Practice Sentence 🎯",
                key="generate-btn",
                type="primary",
                use_container_width=True,
                help="Click to generate a new practice sentence"
            ):
                with st.spinner("Generating sentence..."):
                    try:
                        sentence_data = self.generate_sentence()
                        if sentence_data:
                            self.cache_sentence(sentence_data)
                            st.session_state.current_sentence = sentence_data
                            st.session_state.current_english = sentence_data.get('english', '')
                            st.session_state.app_state = AppState.PRACTICE
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error generating sentence: {e}")
                        st.error("Failed to generate sentence. Please try again.")

    def generate_sentence(self):
        """Generate a sentence using the LLM"""
        if not self.prompts.get('sentence_generation'):
            logger.error("Sentence generation prompts not loaded")
            return None

        current_group = next(
            (g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id),
            None
        )
        if not current_group:
            logger.error("No current group selected")
            return None

        system_prompt = self.prompts['sentence_generation']['system']
        user_prompt = self.prompts['sentence_generation']['user'].format(
            category=current_group['name']
        )

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "max_tokens": 50
                },
                timeout=10
            )
            response.raise_for_status()
            generated_text = response.json()['response']

            lines = generated_text.split('\n')
            japanese_sentence = lines[0].strip() if len(lines) > 0 else ""
            english_translation = lines[1].strip() if len(lines) > 1 else ""

            return {
                "japanese": japanese_sentence,
                "english": english_translation,
                "level": current_group['level'],
                "category": current_group['name']
            }
        except requests.RequestException as e:
            logger.error(f"Failed to generate sentence: {e}")
            return None

    def cache_sentence(self, sentence_data):
        """Cache the generated sentence"""
        try:
            self.execute_query(
                "INSERT INTO sentences (japanese, english, level, category) VALUES (?, ?, ?, ?)",
                (
                    sentence_data['japanese'],
                    sentence_data['english'],
                    sentence_data['level'],
                    sentence_data['category']
                )
            )
            logger.info(f"Cached sentence: {sentence_data['japanese']}")
        except sqlite3.Error as e:
            logger.error(f"Failed to cache sentence: {e}")

    def recognize_text(self, image):
        """Recognize text from image using OCR"""
        if self.mocr is None:
            self.mocr = MangaOcr()
        return self.mocr(image)

    def grade_submission(self, submitted_text, correct_text):
        """Grade the user's submission"""
        if submitted_text.strip() == correct_text.strip():
            grade = 'S'
        elif submitted_text.strip() in correct_text.strip():
            grade = 'A'
        elif correct_text.strip() in submitted_text.strip():
            grade = 'B'
        else:
            grade = 'C'

        return {
            'grade': grade,
            'submitted_text': submitted_text,
            'correct_text': correct_text,
            'feedback': self.generate_feedback(submitted_text, correct_text, grade)
        }

    def generate_feedback(self, submitted_text, correct_text, grade):
        """Generate feedback based on grade"""
        feedbacks = {
            'S': "Perfect! Your writing matches exactly!",
            'A': "Very good! Your writing is mostly correct.",
            'B': "Good attempt! Keep practicing to improve accuracy.",
            'C': "Keep practicing! Focus on stroke order and character formation."
        }
        return feedbacks.get(grade, "Unknown grade")

    def process_submission(self, recognized_text):
        """Process the user's submission"""
        if st.session_state.current_sentence:
            correct_text = st.session_state.current_sentence['japanese']
            review_data = self.grade_submission(recognized_text, correct_text)
            st.session_state.review_data = review_data
            st.session_state.app_state = AppState.REVIEW
            st.rerun()

    def render_practice_state(self):
        """Render the practice state UI"""
        self.set_background("1371442.png")
        st.title("Japanese Writing Practice")

        if not st.session_state.current_sentence:
            st.warning("No practice sentence generated yet.")
            if st.button("Back to Categories"):
                st.session_state.app_state = AppState.SETUP
                st.rerun()
            return

        st.markdown(
            """
            <style>
            .sentence-box {
                padding: 20px;
                border-radius: 10px;
                background-color: #f0f2f6;
                margin: 20px 0;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sentence-box">', unsafe_allow_html=True)
        st.markdown("### Practice this sentence:")
        st.markdown(f"**Japanese:** {st.session_state.current_sentence['japanese']}")
        st.markdown(f"**English:** {st.session_state.current_english}")
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["Draw", "Webcam", "Upload"])

        with tab1:
            st.subheader("Draw your sentence:")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",
                stroke_width=2,
                stroke_color='#0000',
                background_color="#eee",
                height=200,
                width=600,
                drawing_mode="freedraw",
                key="canvas",
            )

            if st.button("Submit Drawing"):
                if canvas_result.image_data is not None:
                    img = Image.fromarray(np.uint8(canvas_result.image_data))
                    recognized_text = self.recognize_text(img)
                    self.process_submission(recognized_text)

        with tab2:
            st.subheader("Capture your written response:")
            picture = st.camera_input("Hold up your written response")
            if picture:
                image = Image.open(picture)
                recognized_text = self.recognize_text(image)
                if st.button("Grade Submission (Camera)"):
                    self.process_submission(recognized_text)

        with tab3:
            st.subheader("Upload your written response:")
            uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                recognized_text = self.recognize_text(image)
                if st.button("Grade Submission (Upload)"):
                    self.process_submission(recognized_text)

        st.markdown("---")
        if st.button("Back to Categories"):
            st.session_state.app_state = AppState.SETUP
            st.rerun()

    def render_review_state(self):
        """Render the review state UI"""
        self.set_background("1371443.png")
        st.title("Review Your Writing")

        if st.session_state.review_data:
            review_data = st.session_state.review_data
            grade_colors = {
                'S': '#FFD700',
                'A': '#98FB98',
                'B': '#87CEEB',
                'C': '#FFA07A'
            }

            st.markdown(f"""
                <style>
                .grade-box {{
                    padding: 20px;
                    border-radius: 10px;
                    background-color: {grade_colors[review_data['grade']]};
                    text-align: center;
                    margin: 20px 0;
                }}
                </style>
                """, unsafe_allow_html=True)

            st.markdown(f'<div class="grade-box"><h1>Grade: {review_data["grade"]}</h1></div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Your Writing:")
                st.info(review_data['submitted_text'])
            with col2:
                st.markdown("#### Correct Text:")
                st.success(review_data['correct_text'])

            st.markdown("### Feedback")
            st.info(review_data['feedback'])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Try Again"):
                    st.rerun()
            with col2:
                if st.button("New Sentence"):
                    st.session_state.app_state = AppState.SETUP
                    st.rerun()
        else:
            st.warning("No review data found.")

    def run(self):
        """Main application runner"""
        try:
            if st.session_state.debug_mode:
                with st.expander("Debug Information"):
                    st.write("### Session State", dict(st.session_state))
                    st.write("### Error Log")
                    for error in st.session_state.error_log[-5:]:
                        st.error(error)

            if st.session_state.app_state == AppState.SETUP:
                self.render_setup_state()
            elif st.session_state.app_state == AppState.PRACTICE:
                self.render_practice_state()
            elif st.session_state.app_state == AppState.REVIEW:
                self.render_review_state()

        except Exception as e:
            error_msg = f"Application error: {str(e)}"
            logger.error(error_msg)
            st.session_state.error_log.append(error_msg)
            st.error("An unexpected error occurred. Please refresh the page.")

if __name__ == "__main__":
    app = WritingPracticeApp()
    app.run()