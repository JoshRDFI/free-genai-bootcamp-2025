# writing-practice/app.py
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

# ---------- Path Configuration ----------
# Corrected based on project layout and your feedback
BASE_DIR = Path(__file__).parent.absolute()  # writing-practice directory
PROJECT_ROOT = BASE_DIR.parent        # free-genai-bootcamp-2025 directory
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
IMAGES_DIR = BASE_DIR / "images"

# ---------- Database Schema Constants ----------
REQUIRED_TABLES = {
    'word_groups': ['id', 'name', 'level'],
    'words': ['id', 'kanji', 'romaji', 'english', 'group_id', 'correct_count', 'wrong_count'],
    'sentences': ['id', 'japanese', 'english', 'level', 'category'],  # Now matches actual schema
    'writing_submissions': ['id', 'sentence_id', 'transcription', 'translation', 'grade', 'feedback']  # Add this line
}

# ---------- Logging Configuration ----------
LOG_FILE = BASE_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ],
)
logging.getLogger('watchdog').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ---------- Application States ----------
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class WritingPracticeApp:
    def __init__(self):
        self.initialize_session_state()
        self.load_prompts()
        self.validate_database()
        self.load_vocabulary_groups()
        self.mocr = None
        self.start_api_server_if_needed()

    # ---------- Core Initialization Methods ----------
    def initialize_session_state(self):
        """Initialize all session state variables"""
        defaults = {
            'app_state': AppState.SETUP,
            'current_sentence': None,
            'current_english': "",
            'review_data': None,
            'current_group_id': None,
            'vocabulary': [],
            'error_log': []
        }

        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def validate_database(self):
        """Validate database structure against schema.sql"""
        try:
            # Verify database file existence
            if not DB_PATH.exists():
                raise FileNotFoundError(f"Database file not found at {DB_PATH}")

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                # Verify table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}

                missing_tables = set(REQUIRED_TABLES.keys()) - existing_tables
                if missing_tables:
                    raise ValueError(f"Missing tables: {', '.join(missing_tables)}")

                # Verify table columns
                for table, expected_columns in REQUIRED_TABLES.items():
                    cursor.execute(f"PRAGMA table_info({table})")
                    existing_columns = {row[1] for row in cursor.fetchall()}
                    missing_columns = set(expected_columns) - existing_columns

                    if missing_columns:
                        raise ValueError(
                            f"Table '{table}' missing columns: {', '.join(missing_columns)}"
                        )

                logger.info("Database schema validation passed")

        except Exception as e:
            logger.critical(f"Database validation failed: {str(e)}")
            st.error("Critical database error - check logs")
            st.stop()

    # ---------- API Server Methods ----------
    def start_api_server_if_needed(self):
        """Check if API server is running, start if not"""
        try:
            requests.get("http://localhost:5000/api/health", timeout=2)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self.start_api_server()

    def start_api_server(self):
        """Start Flask API server with proper endpoints"""
        app = Flask(__name__)

        @app.route('/api/health')
        def health_check():
            return jsonify({"status": "ok"})

        @app.route('/api/groups/<int:group_id>/raw')
        def get_group_words(group_id):
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, kanji, romaji, english
                        FROM words
                        WHERE group_id = ?
                    """, (group_id,))
                    return jsonify([dict(row) for row in cursor.fetchall()])
            except Exception as e:
                logger.error(f"API error: {e}")
                return jsonify({"error": str(e)}), 500

        threading.Thread(
            target=app.run,
            kwargs={'port': 5000, 'use_reloader': False},
            daemon=True
        ).start()
        logger.info("Started background API server on port 5000")

    # ---------- UI Rendering Methods ----------
    def set_background(self, image_name: str):
        """Set background image with validation"""
        try:
            bg_path = IMAGES_DIR / image_name
            if not bg_path.exists():
                raise FileNotFoundError(f"Background image missing: {bg_path.name}")

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
                    margin: 2rem auto;
                    max-width: 90%;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        except Exception as e:
            logger.error(f"Background error: {e}")
            st.markdown("""<style>.stApp { background-color: #f0f2f6; }</style>""",
                       unsafe_allow_html=True)

    def render_setup_state(self):
        """Render category selection interface"""
        self.set_background("1240417.png")
        st.title("Japanese Writing Practice")

        if not self.vocabulary_groups:
            st.error("No vocabulary categories found in database")
            return

        # Category selection grid
        cols = st.columns(3)
        for idx, group in enumerate(self.vocabulary_groups):
            with cols[idx % 3]:
                if st.button(
                    f"{group['name']}\n({group['level']})",
                    key=f"group_{group['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_group_id = group['id']
                    self.load_vocabulary(group['id'])
                    st.rerun()

        # Generate button section
        if group_id := st.session_state.current_group_id:
            selected = next((g for g in self.vocabulary_groups if g['id'] == group_id), None)
            if not selected:
                st.error("Invalid category selection")
                return

            st.markdown("---")
            st.markdown(f"**Selected Category:** {selected['name']}")

            if st.button(
                "Generate Practice Sentence 🎯",
                type="primary",
                use_container_width=True,
                key="generate-btn"
            ):
                with st.spinner("Generating sentence..."):
                    if sentence := self.generate_sentence():
                        self.cache_sentence(sentence)
                        st.session_state.update({
                            'current_sentence': sentence,
                            'app_state': AppState.PRACTICE
                        })
                        st.rerun()

    def render_practice_state(self):
        """Render the practice writing interface"""
        self.set_background("1371442.png")
        st.title("Practice Writing")

        if not st.session_state.current_sentence:
            st.error("No active practice session")
            st.session_state.app_state = AppState.SETUP
            st.rerun()
            return

        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Current Sentence")
            st.markdown(f"""
                **Japanese:**
                {st.session_state.current_sentence['japanese']}
                **English:**
                {st.session_state.current_sentence['english']}
            """)

        with col2:
            st.subheader("Write Your Response")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",
                stroke_width=2,
                stroke_color='#000',
                background_color="#ffffff",
                height=300,
                width=400,
                drawing_mode="freedraw",
                key="canvas"
            )

        if st.button("Submit for Review"):
            if canvas_result.image_data is not None:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'))
                recognized_text = self.recognize_text(img)
                self.process_submission(recognized_text)

        if st.button("Back to Categories"):
            st.session_state.app_state = AppState.SETUP
            st.rerun()

    def render_review_state(self):
        """Render the submission review interface"""
        self.set_background("1371443.png")
        st.title("Submission Review")

        if not st.session_state.review_data:
            st.error("No review data available")
            st.session_state.app_state = AppState.SETUP
            st.rerun()
            return

        review = st.session_state.review_data
        grade_color = {
            'S': '#4CAF50',
            'A': '#8BC34A',
            'B': '#FFC107',
            'C': '#F44336'
        }.get(review['grade'], '#607D8B')

        st.markdown(f"""
            <style>
            .grade-box {{
                background-color: {grade_color};
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                margin: 1rem 0;
            }}
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="grade-box">
                <h2>Grade: {review['grade']}</h2>
                <p>{review['feedback']}</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Your Submission")
            st.text_area("", value=review['submitted_text'], disabled=True)

        with col2:
            st.subheader("Correct Answer")
            st.text_area("", value=review['correct_text'], disabled=True)

        if st.button("Try Again"):
            st.session_state.app_state = AppState.PRACTICE
            st.rerun()

        if st.button("New Sentence"):
            st.session_state.app_state = AppState.SETUP
            st.rerun()

    # ---------- Core Functionality Methods ----------
    def load_prompts(self):
        """Load generation prompts from YAML file"""
        try:
            with open(BASE_DIR / "prompts.yaml", "r") as f:
                self.prompts = yaml.safe_load(f)
                logger.info("Prompts loaded successfully")
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            self.prompts = {}
            st.error("Failed to load prompt configurations")

    def load_vocabulary_groups(self):
        """Load vocabulary groups from database"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, level
                    FROM word_groups
                    ORDER BY level
                """)
                self.vocabulary_groups = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Loaded {len(self.vocabulary_groups)} vocabulary groups")
        except Exception as e:
            logger.error(f"Error loading vocabulary groups: {e}")
            self.vocabulary_groups = []
            st.error("Failed to load vocabulary categories")

    def load_vocabulary(self, group_id: int):
        """Load vocabulary for selected group"""
        try:
            response = requests.get(
                f"http://localhost:5000/api/groups/{group_id}/raw",
                timeout=5
            )
            if response.ok:
                st.session_state.vocabulary = response.json()
                logger.info(f"Loaded {len(st.session_state.vocabulary)} words via API")
                return
        except Exception as e:
            logger.warning(f"API load failed: {e}, falling back to direct DB access")

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, kanji, romaji, english
                    FROM words
                    WHERE group_id = ?
                """, (group_id,))
                st.session_state.vocabulary = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Loaded {len(st.session_state.vocabulary)} words from DB")
        except Exception as e:
            logger.error(f"Vocabulary load failed: {e}")
            st.error("Failed to load vocabulary")

    def generate_sentence(self):
        """Generate practice sentence using vocabulary"""
        if not st.session_state.vocabulary:
            st.error("No vocabulary loaded for selected category")
            return None

        try:
            # Example generation logic - replace with your actual implementation
            selected_words = random.sample(st.session_state.vocabulary, 3)
            sentence_jp = " ".join(word['kanji'] for word in selected_words) + "。"
            sentence_en = " ".join(word['english'] for word in selected_words) + "."

            return {
                "japanese": sentence_jp,
                "english": sentence_en,
                "level": "N5",  # Get from group
                "category": "Sample"  # Get from group
            }
        except Exception as e:
            logger.error(f"Sentence generation failed: {e}")
            return None

    def cache_sentence(self, sentence_data):
        """Store generated sentence in database"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sentences (japanese, english, level, category)
                    VALUES (?, ?, ?, ?)
                """, (
                    sentence_data['japanese'],
                    sentence_data['english'],
                    sentence_data['level'],
                    sentence_data['category']
                ))
                conn.commit()
                logger.info("Cached generated sentence")
        except Exception as e:
            logger.error(f"Failed to cache sentence: {e}")

    def recognize_text(self, image):
        """Perform OCR on handwritten text"""
        if self.mocr is None:
            self.mocr = MangaOcr()
        return self.mocr(image)

    def process_submission(self, recognized_text):
        """Process user submission and grade it"""
        correct_text = st.session_state.current_sentence['japanese']

        # Simple grading logic - enhance as needed
        if recognized_text.strip() == correct_text.strip():
            grade = 'S'
        else:
            grade = 'C'

        st.session_state.review_data = {
            'grade': grade,
            'submitted_text': recognized_text,
            'correct_text': correct_text,
            'feedback': self.generate_feedback(grade)
        }
        st.session_state.app_state = AppState.REVIEW
        st.rerun()

    def generate_feedback(self, grade):
        """Generate feedback based on grade"""
        return {
            'S': "Perfect! Your writing matches exactly!",
            'A': "Very close! Minor improvements needed.",
            'B': "Good attempt. Practice stroke order.",
            'C': "Needs work. Compare with correct answer."
        }.get(grade, "Unknown grade")

    def run(self):
        """Main application loop"""
        try:
            if st.session_state.app_state == AppState.SETUP:
                self.render_setup_state()
            elif st.session_state.app_state == AppState.PRACTICE:
                self.render_practice_state()
            elif st.session_state.app_state == AppState.REVIEW:
                self.render_review_state()
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error("A critical error occurred. Please refresh the page.")

if __name__ == "__main__":
    WritingPracticeApp().run()