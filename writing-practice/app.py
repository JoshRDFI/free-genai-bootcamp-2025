import streamlit as st
import sqlite3
import logging
import random
import json
import yaml
from pathlib import Path
import requests
import io
from PIL import Image
import importlib.util
import os
import numpy as np

# Force CPU mode for MangaOCR
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ---- Path Configuration ----
BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
SENTENCES_PATH = BASE_DIR / "sentences.json"
PROMPTS_PATH = BASE_DIR / "prompts.yaml"

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

# Check if a package is installed
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Check required packages
required_packages = {
    "streamlit_drawable_canvas": "streamlit-drawable-canvas",
    "manga_ocr": "manga-ocr"
}

missing_packages = []
for module_name, package_name in required_packages.items():
    if not is_package_installed(module_name):
        missing_packages.append(package_name)

if missing_packages:
    st.error("Missing required packages. Please install them using:")
    st.code(f"pip install {' '.join(missing_packages)}")
    st.stop()

# Now it's safe to import
from streamlit_drawable_canvas import st_canvas
import manga_ocr

# Initialize MangaOCR
@st.cache_resource
def get_ocr():
    try:
        logger.info("Initializing MangaOCR in CPU mode")
        return manga_ocr.MangaOcr()
    except Exception as e:
        logger.error(f"Error initializing MangaOCR: {e}")
        return None

# Load prompts from YAML file
def load_prompts():
    try:
        with open(PROMPTS_PATH, 'r') as file:
            prompts = yaml.safe_load(file)
            logger.info("Prompts loaded successfully")
            return prompts
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        return {}

# Load sample sentences
def load_sample_sentences():
    try:
        if SENTENCES_PATH.exists():
            with open(SENTENCES_PATH, "r") as f:
                return json.load(f)
        else:
            logger.warning("Sentences file not found, creating empty file")
            with open(SENTENCES_PATH, "w") as f:
                json.dump([], f)
            return []
    except Exception as e:
        logger.error(f"Error loading sample sentences: {e}")
        return []

# Save sentence to JSON file
def save_sentence(sentence_data):
    try:
        sentences = load_sample_sentences()
        sentences.append(sentence_data)
        with open(SENTENCES_PATH, "w") as f:
            json.dump(sentences, f, indent=2)
        logger.info(f"Saved sentence to {SENTENCES_PATH}")
    except Exception as e:
        logger.error(f"Error saving sentence: {e}")

# Process image with MangaOCR
def process_image_with_ocr(image):
    ocr = get_ocr()
    if ocr is None:
        return "OCR not available"

    try:
        # Convert to PIL Image if it's not already
        if not isinstance(image, Image.Image):
            image = Image.open(image)

        # Save to a temporary file (MangaOCR works better with files)
        temp_path = "temp_image.png"
        image.save(temp_path)

        # Process with OCR
        text = ocr(temp_path)

        # Clean up
        if Path(temp_path).exists():
            Path(temp_path).unlink()

        return text
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return "Error processing image"

# Translate Japanese text to English
def translate_text(text, prompts):
    try:
        system_prompt = prompts['translation']['system']
        user_prompt = prompts['translation']['user'].format(text=text)

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Translation not available")
    except Exception as e:
        logger.warning(f"Translation error: {e}")

    return "Translation not available"

# Grade user response
def grade_response(target_sentence, submission, translation, prompts):
    try:
        system_prompt = prompts['grading']['system']
        user_prompt = prompts['grading']['user'].format(
            target_sentence=target_sentence,
            submission=submission,
            translation=translation
        )

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Grading not available")
    except Exception as e:
        logger.warning(f"Grading error: {e}")

    # Fallback grading
    if submission.strip() == "":
        return "Grade: C\nFeedback: No response provided."
    elif submission.strip() == target_sentence.strip():
        return "Grade: S\nFeedback: Perfect match with the original sentence!"
    else:
        # Simple character-based similarity
        similarity = len(set(submission) & set(target_sentence)) / len(set(target_sentence))
        if similarity > 0.8:
            grade = "A"
        elif similarity > 0.5:
            grade = "B"
        else:
            grade = "C"
        return f"Grade: {grade}\nFeedback: Your response has approximately {int(similarity*100)}% character overlap with the original."

# Generate sentence using Ollama
def generate_sentence(category, word, prompts):
    try:
        system_prompt = prompts['sentence_generation']['system']
        user_prompt = prompts['sentence_generation']['user'].format(word=word)

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json().get("response", "")

            # Extract Japanese and English sentences
            lines = result.strip().split('\n')
            japanese = ""
            english = ""

            for line in lines:
                if line.startswith("Japanese:"):
                    japanese = line.replace("Japanese:", "").strip()
                elif line.startswith("English:"):
                    english = line.replace("English:", "").strip()

            if japanese and english:
                return {
                    "japanese": japanese,
                    "english": english,
                    "category": category,
                    "level": "N5"  # Default level
                }
    except Exception as e:
        logger.error(f"Error generating sentence: {e}")

    # Fallback to sample sentences
    sample_sentences = load_sample_sentences()
    if sample_sentences:
        return random.choice(sample_sentences)

    # Ultimate fallback
    return {
        "japanese": "これは日本語の文です。",
        "english": "This is a Japanese sentence.",
        "level": "N5",
        "category": "Fallback"
    }

# Initialize session state
if 'app_state' not in st.session_state:
    st.session_state.app_state = "setup"

if 'current_sentence' not in st.session_state:
    st.session_state.current_sentence = None

if 'current_group_id' not in st.session_state:
    st.session_state.current_group_id = None

if 'review_data' not in st.session_state:
    st.session_state.review_data = None

if 'vocabulary_groups' not in st.session_state:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, level FROM word_groups ORDER BY level")
            st.session_state.vocabulary_groups = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(st.session_state.vocabulary_groups)} vocabulary groups")
    except Exception as e:
        logger.error(f"Error loading groups: {e}")
        st.session_state.vocabulary_groups = []

# Load prompts
prompts = load_prompts()

# Main app
st.title("Japanese Writing Practice")

# SETUP STATE
if st.session_state.app_state == "setup":
    # Display vocabulary groups as buttons
    if not st.session_state.vocabulary_groups:
        st.error("No vocabulary categories found")
    else:
        st.subheader("Select a Category")

        # Create columns for buttons (3 columns)
        cols = st.columns(3)

        for i, group in enumerate(st.session_state.vocabulary_groups):
            col_idx = i % 3
            with cols[col_idx]:
                # Determine if this button is selected
                is_selected = st.session_state.current_group_id == group['id']

                # Custom button styling
                button_style = f"""
                <style>
                div[data-testid="stButton"] button[key="group_{group['id']}"] {{
                    background-color: {'#1f77b4' if is_selected else 'white'};
                    color: {'white' if is_selected else 'black'};
                    border: 2px solid #1f77b4;
                    margin: 5px 0;
                    min-height: 60px;
                }}
                </style>
                """
                st.markdown(button_style, unsafe_allow_html=True)

                if st.button(
                    f"{group['name']} ({group.get('level', 'N/A')})",
                    key=f"group_{group['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_group_id = group['id']
                    st.rerun()

        # Display current category info and generate button
        if st.session_state.current_group_id:
            st.markdown("---")
            selected_name = next(
                (g['name'] for g in st.session_state.vocabulary_groups if g['id'] == st.session_state.current_group_id),
                ''
            )
            st.info(f"Selected: {selected_name}")

            # Fetch words for the selected group
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
                        (st.session_state.current_group_id,)
                    )
                    words = [dict(row) for row in cursor.fetchall()]

                    if words:
                        # Select a random word
                        selected_word = random.choice(words)

                        if st.button("Generate Practice Sentence 🎯", type="primary", use_container_width=True):
                            with st.spinner("Generating sentence..."):
                                # Generate sentence using the selected word
                                sentence_data = generate_sentence(
                                    selected_name,
                                    selected_word['kanji'],
                                    prompts
                                )

                                if sentence_data:
                                    # Save to JSON file
                                    save_sentence(sentence_data)

                                    # Update session state
                                    st.session_state.current_sentence = sentence_data
                                    st.session_state.app_state = "practice"
                                    st.rerun()
                    else:
                        st.warning(f"No words found for category: {selected_name}")
            except Exception as e:
                logger.error(f"Error fetching words: {e}")
                st.error("Failed to fetch words for this category")

# PRACTICE STATE
elif st.session_state.app_state == "practice":
    if not st.session_state.current_sentence:
        st.warning("No practice sentence is generated yet.")
        if st.button("Back to Categories"):
            st.session_state.app_state = "setup"
            st.rerun()
    else:
        st.subheader("Current Sentence")
        st.markdown(f"""
        **Japanese:**
        {st.session_state.current_sentence['japanese']}
        **English:**
        {st.session_state.current_sentence['english']}
        """)

        # Add a writing area
        st.subheader("Submit Your Response")

        # Create tabs for different input methods
        tab1, tab2, tab3 = st.tabs(["Draw Response", "Upload Image", "Take Photo"])

        with tab1:
            st.write("Draw your response below:")

            # Create a canvas for drawing
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#ffffff",
                height=300,
                width=600,
                drawing_mode="freedraw",
                key="canvas",
            )

            if st.button("Submit Drawing"):
                if canvas_result.image_data is not None:
                    # Convert the canvas image to PIL Image
                    img_array = canvas_result.image_data
                    if img_array.sum() > 0:  # Check if the canvas has any drawing
                        # Display the image
                        st.image(Image.fromarray(img_array.astype('uint8'), 'RGBA'), caption="Your Drawing", use_container_width=True)

                        try:
                            # Process with OCR
                            recognized_text = process_image_with_ocr(Image.fromarray(img_array.astype('uint8'), 'RGBA'))
                            st.write(f"Recognized text: {recognized_text}")

                            # Translate the recognized text
                            translation = translate_text(recognized_text, prompts)

                            # Grade the response
                            feedback = grade_response(
                                st.session_state.current_sentence['english'],
                                recognized_text,
                                translation,
                                prompts
                            )

                            # Store review data
                            st.session_state.review_data = {
                                'transcription': recognized_text,
                                'translation': translation,
                                'feedback': feedback,
                                'original_japanese': st.session_state.current_sentence['japanese'],
                                'original_english': st.session_state.current_sentence['english']
                            }

                            # Transition to review state
                            st.session_state.app_state = "review"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing image: {e}")
                    else:
                        st.warning("Please draw something before submitting.")
                else:
                    st.warning("Please draw something before submitting.")

        with tab2:
            uploaded_file = st.file_uploader("Upload an image of your handwritten response", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                # Display the uploaded image
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_container_width=True)

                if st.button("Submit Uploaded Image"):
                    try:
                        # Process with OCR
                        recognized_text = process_image_with_ocr(uploaded_file)
                        st.write(f"Recognized text: {recognized_text}")

                        # Translate the recognized text
                        translation = translate_text(recognized_text, prompts)

                        # Grade the response
                        feedback = grade_response(
                            st.session_state.current_sentence['english'],
                            recognized_text,
                            translation,
                            prompts
                        )

                        # Store review data
                        st.session_state.review_data = {
                            'transcription': recognized_text,
                            'translation': translation,
                            'feedback': feedback,
                            'original_japanese': st.session_state.current_sentence['japanese'],
                            'original_english': st.session_state.current_sentence['english']
                        }

                        # Transition to review state
                        st.session_state.app_state = "review"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing image: {e}")

        with tab3:
            st.write("Take a photo of your handwritten response")
            picture = st.camera_input("Take a picture")

            if picture:
                # Display the captured image
                st.image(picture, caption="Captured Image", use_container_width=True)

                if st.button("Submit Photo"):
                    try:
                        # Process with OCR
                        recognized_text = process_image_with_ocr(picture)
                        st.write(f"Recognized text: {recognized_text}")

                        # Translate the recognized text
                        translation = translate_text(recognized_text, prompts)

                        # Grade the response
                        feedback = grade_response(
                            st.session_state.current_sentence['english'],
                            recognized_text,
                            translation,
                            prompts
                        )

                        # Store review data
                        st.session_state.review_data = {
                            'transcription': recognized_text,
                            'translation': translation,
                            'feedback': feedback,
                            'original_japanese': st.session_state.current_sentence['japanese'],
                            'original_english': st.session_state.current_sentence['english']
                        }

                        # Transition to review state
                        st.session_state.app_state = "review"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing image: {e}")

        # Back button
        if st.button("Back to Categories", use_container_width=True):
            st.session_state.app_state = "setup"
            st.rerun()

# REVIEW STATE
elif st.session_state.app_state == "review":
    if not st.session_state.review_data:
        st.warning("No review data available.")
        if st.button("Back to Categories"):
            st.session_state.app_state = "setup"
            st.rerun()
    else:
        review_data = st.session_state.review_data

        st.subheader("Review Your Writing")

        # Extract grade from feedback
        grade = "C"  # Default grade
        feedback_text = review_data['feedback']

        if "Grade:" in feedback_text:
            grade_line = [line for line in feedback_text.split('\n') if "Grade:" in line]
            if grade_line:
                grade = grade_line[0].split("Grade:")[1].strip().split()[0]

        # Define grade colors
        grade_colors = {
            'S': '#FFD700',  # Gold
            'A': '#98FB98',  # Pale green
            'B': '#87CEEB',  # Sky blue
            'C': '#FFA07A'   # Light salmon
        }

        # Display grade with color
        st.markdown(f"""
        <style>
        .grade-box {{
            padding: 20px;
            border-radius: 10px;
            background-color: {grade_colors.get(grade, '#FFA07A')};
            text-align: center;
            margin: 20px 0;
        }}
        </style>
        <div class="grade-box">
        <h1>Grade: {grade}</h1>
        </div>
        """, unsafe_allow_html=True)

        # Display original sentence and transcription
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original Sentence:**")
            st.markdown(f"Japanese: {review_data['original_japanese']}")
            st.markdown(f"English: {review_data['original_english']}")

        with col2:
            st.markdown("**Your Response:**")
            st.markdown(f"Transcription: {review_data['transcription']}")
            st.markdown(f"Translation: {review_data['translation']}")

        # Display feedback
        st.subheader("Feedback")

        # Extract feedback text without the grade
        if "Feedback:" in feedback_text:
            feedback_parts = feedback_text.split("Feedback:")
            if len(feedback_parts) > 1:
                feedback_only = feedback_parts[1].strip()
                st.info(feedback_only)
            else:
                st.info(feedback_text)
        else:
            st.info(feedback_text)

        # Navigation buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Try Again", use_container_width=True):
                st.session_state.app_state = "practice"
                st.session_state.review_data = None
                st.rerun()

        with col2:
            if st.button("New Sentence", use_container_width=True):
                st.session_state.app_state = "setup"
                st.session_state.current_sentence = None
                st.session_state.review_data = None
                st.rerun()