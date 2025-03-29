import streamlit as st
import requests
import sqlite3
import logging
import random
import datetime
from enum import Enum
from pathlib import Path
from PIL import Image
from manga_ocr import MangaOcr
from streamlit_drawable_canvas import st_canvas
import ollama  # Add this import for LLM interaction

# ---- Path Configuration ----
BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
IMAGES_DIR = BASE_DIR / "images"

# ---- Database Schema ----
REQUIRED_TABLES = {
    'word_groups': ['id', 'name', 'level'],
    'words': ['id', 'kanji', 'romaji', 'english', 'group_id'],
    'sentences': ['id', 'japanese', 'english', 'level', 'category'],
    'writing_submissions': ['id', 'sentence_id', 'transcription', 'translation', 'grade', 'feedback']
}

# ---- Logging Configuration ----
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---- API Health Check ----
def check_api_health():
    """Check if JSON API server is running"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False

# ---- LLM Health Check ----
def check_llm_health():
    """Check if LLM server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False

# ---- Application States ----
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class WritingPracticeApp:
    def __init__(self):
        self.initialize_session_state()
        self.load_vocabulary_groups()
        self.mocr = None
        self.error_log = []

    def initialize_session_state(self):
        defaults = {
            'app_state': AppState.SETUP,
            'current_sentence': None,
            'review_data': None,
            'current_group_id': None,
            'vocabulary': []
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def validate_database(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}
                missing_tables = set(REQUIRED_TABLES.keys()) - existing_tables
                if missing_tables:
                    raise ValueError(f"Missing tables: {', '.join(missing_tables)}")
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            st.error("Database configuration error")
            st.stop()

    def set_background(self, image_name: str):
        try:
            bg_path = IMAGES_DIR / image_name
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
            st.markdown("""<style>.stApp { background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)

    def render_setup_state(self):
        self.set_background("1240417.png")
        st.title("Japanese Writing Practice")

        # API and LLM status indicators
        api_status = "🟢 Running" if check_api_health() else "🔴 Offline"
        llm_status = "🟢 Running" if check_llm_health() else "🔴 Offline"
        st.markdown(f"**API Status:** {api_status}")
        st.markdown(f"**LLM Status:** {llm_status}")

        if not self.vocabulary_groups:
            st.error("No vocabulary categories found")
            return

        if not check_api_health():
            st.warning("""
            **Connection Issue Detected**
            Trying fallback database access. Some features might be limited.
            - Ensure the API server is running in another terminal:
            `python api_server.py`
            - Check firewall settings if running remotely
            """)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Generate Random Practice Sentence 🎯",
                type="primary",
                use_container_width=True,
                key="generate-btn"
            ):
                try:
                    # Select random group excluding "Random Mix"
                    valid_groups = [g for g in self.vocabulary_groups if g['id'] != -1]
                    selected_group = random.choice(valid_groups)
                    self.load_vocabulary(selected_group['id'])

                    with st.spinner("Generating sentence..."):
                        if sentence := self.generate_sentence():
                            self.cache_sentence(sentence)
                            st.session_state.update({
                                'current_sentence': sentence,
                                'app_state': AppState.PRACTICE,
                                'current_group_id': selected_group['id']
                            })
                            st.rerun()
                        else:
                            st.error("Failed to generate sentence")
                except Exception as e:
                    logger.error(f"Generation failed: {e}")
                    st.error("Error generating practice session")

        # Display current category if available
        if st.session_state.get('current_group_id'):
            try:
                group = next(g for g in self.vocabulary_groups if g['id'] == st.session_state.current_group_id)
                st.markdown(f"*Last practiced: {group['name']} (Level {group['level']})*")
            except StopIteration:
                pass

    # ... (rest of the class remains unchanged)

    def run(self):
        self.validate_database()
        try:
            if st.session_state.app_state == AppState.SETUP:
                self.render_setup_state()
            elif st.session_state.app_state == AppState.PRACTICE:
                self.render_practice_state()
            elif st.session_state.app_state == AppState.REVIEW:
                self.render_review_state()
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error("A critical error occurred. Please refresh the page.")

if __name__ == "__main__":
    WritingPracticeApp().run()