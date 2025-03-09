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
        self.mocr = None  # Initialize MangaOCR on demand

        # Start the API server only if it's not already running
        try:
            response = requests.get("http://localhost:5000/api/groups/1/raw")
            if response.status_code != 200:
                self.start_api_server()
        except requests.exceptions.ConnectionError:
            self.start_api_server()

    def start_api_server(self):
        """Start the API server on port 5000"""
        app = Flask(__name__)

        @app.route('/api/groups/<int:group_id>/raw')
        def get_group_words(group_id):
            try:
                words = self.execute_query(
                    "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                    (group_id,)
                )
                return jsonify(words)
            except Exception as e:
                logger.error(f"API error: {e}")
                return jsonify({"error": str(e)}), 500

        def run_flask():
            try:
                app.run(port=5000)
            except OSError as e:
                logger.warning(f"Could not start API server: {e}")

        # Start Flask in a separate thread
        threading.Thread(target=run_flask, daemon=True).start()
        logger.info("API server started on port 5000")

    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state['app_state'] = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state['current_sentence'] = ""
        if 'current_english' not in st.session_state:
            st.session_state['current_english'] = ""
        if 'review_data' not in st.session_state:
            st.session_state['review_data'] = None
        if 'current_group_id' not in st.session_state:
            st.session_state['current_group_id'] = None
        if 'current_word' not in st.session_state:
            st.session_state['current_word'] = None
        if 'vocabulary' not in st.session_state:
            st.session_state['vocabulary'] = []

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
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")

            # Check if database is empty
            self.cursor.execute("SELECT COUNT(*) FROM word_groups")
            if self.cursor.fetchone()[0] == 0:
                self.load_sample_data()

        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            st.error("Failed to connect to database")

    def load_sample_data(self):
        """Load sample data if database is empty"""
        try:
            logger.info("Loading sample data...")

            # Insert sample group
            self.cursor.execute(
                "INSERT INTO word_groups (name, level) VALUES (?, ?)",
                ("Basic Starter Words", "N5")
            )

            # Insert sample words
            sample_words = [
                ("こんにちは", "konnichiwa", "Hello", 1),
                ("ありがとう", "arigatou", "Thank you", 1),
                ("さようなら", "sayounara", "Goodbye", 1)
            ]
            self.cursor.executemany(
                "INSERT INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
                sample_words
            )

            self.conn.commit()
            logger.info("Sample data loaded successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to load sample data: {e}")
            st.error("Failed to initialize sample data")

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
            st.session_state.vocabulary = self.execute_query(
                "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                (group_id,)
            )
            logger.info(f"Loaded {len(st.session_state.vocabulary)} vocabulary items")
        except Exception as e:
            logger.error(f"Error fetching vocabulary: {e}")
            st.error("Failed to load vocabulary")

    def render_setup_state(self):
        """Render the setup state UI"""
        st.sidebar.markdown("### Current Page: Setup")

        st.title("Japanese Writing Practice")
        st.write("Welcome to the Japanese Writing Practice app. Select a category to begin.")

        # Load vocabulary groups if not already loaded
        if not hasattr(self, 'vocabulary_groups') or not self.vocabulary_groups:
            groups_loaded = self.load_vocabulary_groups()
            if not groups_loaded:
                st.warning("Could not load vocabulary categories. Please ensure the main system setup has been completed.")
                return

        # Create columns for buttons
        cols = st.columns(3)

        # Display category buttons in a grid
        if self.vocabulary_groups and len(self.vocabulary_groups) > 0:
            for idx, group in enumerate(self.vocabulary_groups):
                col_idx = idx % 3
                with cols[col_idx]:
                    # Determine if this button is selected
                    is_selected = st.session_state.get('current_group_id') == group['id']

                    # Style for the category button
                    button_style = f"""
                    <style>
                    div[data-testid="stButton"] button[data-testid="baseButton-secondary"] {{
                    background-color: {'#1f77b4' if is_selected else 'white'} !important;
                    color: {'white' if is_selected else 'black'} !important;
                    border: 2px solid #1f77b4 !important;
                    margin: 5px 0 !important;
                    min-height: 60px !important;
                    }}
                    </style>
                    """
                    st.markdown(button_style, unsafe_allow_html=True)

                    if st.button(
                        f"{group['name']}\n({group.get('level', 'N/A')})",
                        key=f"group_{group['id']}",
                        use_container_width=True,
                    ):
                        # Update selected group and fetch vocabulary
                        st.session_state['current_group_id'] = group['id']
                        self.fetch_vocabulary_for_group(group['id'])
        else:
            st.info("No vocabulary categories found. The system may still be initializing.")
            return

        # Display current category info and generate button
        if st.session_state.get('current_group_id'):
            current_group = next((g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id), None)
            if current_group:
                st.markdown("---")
                # Create two columns for the category info and generate button
                info_col, btn_col = st.columns([2, 1])

                with info_col:
                    st.info(f"Selected: {current_group['name']} (JLPT Level: {current_group.get('level', 'N/A')})")
                    vocab_count = len(st.session_state.get('vocabulary', []))
                    st.write(f"This category contains {vocab_count} vocabulary items.")

                with btn_col:
                    # Style for the generate button
                    st.markdown("""
                    <style>
                    div[data-testid="stButton"] button#generate-btn {
                    background-color: #00cc00 !important;
                    color: white !important;
                    border: none !important;
                    font-weight: bold !important;
                    min-height: 60px !important;
                    margin-top: 20px !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # Generate button
                    if st.button("Generate Sentence", key="generate-btn", use_container_width=True):
                        with st.spinner("Generating sentence..."):
                            try:
                                sentence_data = self.generate_sentence()
                                if sentence_data:
                                    self.cache_sentence(sentence_data)
                                    st.session_state['current_sentence'] = sentence_data
                                    st.session_state['current_english'] = sentence_data.get('english', '')
                                    st.session_state['app_state'] = AppState.PRACTICE
                            except Exception as e:
                                logger.error(f"Error generating sentence: {e}")
                                st.error("Failed to generate sentence. Please try again.")

    def generate_sentence(self):
        """Generate a simple JLPT N5 level sentence using the Ollama LLM"""
        if not hasattr(self, 'prompts') or 'sentence_generation' not in self.prompts:
            logger.error("Sentence generation prompts not loaded")
            return None

        current_group = next((g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id), None)
        if not current_group:
            logger.error("No current group selected")
            return None

        # Prepare the prompt for the LLM
        system_prompt = self.prompts['sentence_generation']['system']
        user_prompt = self.prompts['sentence_generation']['user'].format(category=current_group['name'])

        # Send request to Ollama LLM
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "max_tokens": 50  # Limit to short sentences
                },
                timeout=10
            )
            response.raise_for_status()
            generated_text = response.json()['response']

            # Extract Japanese sentence and English translation
            japanese_sentence = generated_text.split('\n')[0].strip()
            english_translation = generated_text.split('\n')[1].strip() if len(generated_text.split('\n')) > 1 else ""

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
        """Cache the generated sentence in the database"""
        try:
            self.execute_query(
                "INSERT INTO sentences (japanese, english, level, category) VALUES (?, ?, ?, ?)",
                (sentence_data['japanese'], sentence_data['english'], sentence_data['level'], sentence_data['category'])
            )
            logger.info(f"Cached sentence: {sentence_data['japanese']}")
        except sqlite3.Error as e:
            logger.error(f"Failed to cache sentence: {e}")

    def recognize_text(self, image):
        """Recognize text from an image using Manga OCR"""
        if self.mocr is None:
            self.mocr = MangaOcr()
        return self.mocr(image)

    def render_practice_state(self):
        """Render the practice state UI with drawing and webcam capture"""
        st.sidebar.markdown("### Current Page: Practice")

        st.title("Japanese Writing Practice")
        st.write("Practice writing the sentence below:")

        if st.session_state.get('current_sentence'):
            st.write(f"**Japanese:** {st.session_state['current_sentence']['japanese']}")
            st.write(f"**English:** {st.session_state['current_english']}")

            # Drawing input method
            st.subheader("Draw your sentence:")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",  # Transparent background
                stroke_width=2,
                stroke_color='#000000',
                background_color="#eee",
                height=200,
                width=600,
                drawing_mode="freedraw",
                key="canvas",
            )

            if st.button("Submit Drawing"):
                if canvas_result.image_data is not None:
                    img_data = canvas_result.image_data
                    img = Image.fromarray(np.uint8(img_data))
                    recognized_text = self.recognize_text(img)
                    st.write(f"Recognized text: {recognized_text}")
                    # TODO: Implement grading for drawn input

            # Webcam capture input method
            st.subheader("Capture your written response with webcam:")
            picture = st.camera_input("Hold up your written response")
            if picture:
                image = Image.open(picture)
                st.image(image, caption="Captured Image", use_column_width=True)
                recognized_text = self.recognize_text(image)
                st.write(f"Recognized text: {recognized_text}")
                # TODO: Implement grading for webcam input

        # Button to go back to setup
        if st.button("Back to Setup"):
            st.session_state['app_state'] = AppState.SETUP

    def render_review_state(self):
        """Render the review state UI"""
        st.sidebar.markdown("### Current Page: Review")

        st.title("Japanese Writing Practice - Review")
        st.write("Review your progress here.")

        # TODO: Implement review functionality
        st.write("Review content goes here.")

        # Button to go back to setup
        if st.button("Back to Setup"):
            st.session_state['app_state'] = AppState.SETUP

    def run(self):
        """Main application runner"""
        try:
            if st.session_state.app_state == AppState.SETUP:
                self.render_setup_state()
            elif st.session_state.app_state == AppState.PRACTICE:
                self.render_practice_state()
            elif st.session_state.app_state == AppState.REVIEW:
                self.render_review_state()
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error("An unexpected error occurred. Please refresh the page.")

# Main entry point
if __name__ == "__main__":
    app = WritingPracticeApp()
    app.run()