import streamlit as st
import requests
import sqlite3
import logging
import random
import json
import yaml
from pathlib import Path
import io
from PIL import Image
import importlib.util
import os
import numpy as np
import time

# ---- Path Configuration ----
BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "shared_db" / "db.sqlite3"
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

# Log startup information
logger.info(f"Starting Streamlit app...")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"DATA_DIR: {DATA_DIR}")
logger.info(f"DB_PATH: {DB_PATH}")
logger.info(f"DB_PATH exists: {DB_PATH.exists()}")
logger.info(f"SENTENCES_PATH: {SENTENCES_PATH}")
logger.info(f"PROMPTS_PATH: {PROMPTS_PATH}")

# Service endpoints
SERVICES = {
    "api": "http://localhost:5000/api/health",
    "mangaocr": "http://localhost:9100/ocr",
    "llm": "http://localhost:9000/v1/chat/completions",
    "embeddings": "http://localhost:6000/health"
}

# Health check endpoints
HEALTH_ENDPOINTS = {
    "api": "http://localhost:5000/api/health",
    "mangaocr": "http://localhost:9100/health",
    "llm": "http://localhost:9000/health",
    "embeddings": "http://localhost:6000/health"
}

def check_service_health(service_name, endpoint, timeout=30):
    """Check if a service is healthy"""
    try:
        # Use health endpoints for checks
        health_endpoint = HEALTH_ENDPOINTS[service_name]
        response = requests.get(health_endpoint, timeout=timeout)
            
        if response.status_code == 200:
            # Check the response content for actual health status
            health_data = response.json()
            if service_name == "mangaocr":
                is_healthy = health_data.get("status") == "healthy"
            elif service_name == "llm":
                is_healthy = health_data.get("status") == "healthy" and health_data.get("ollama_status") == "connected"
            else:
                is_healthy = True  # For other services, 200 is enough
                
            if is_healthy:
                logger.info(f"{service_name} service is healthy")
                return True
            else:
                logger.error(f"{service_name} service reports unhealthy status: {health_data}")
                return False
        else:
            logger.error(f"{service_name} service returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error checking {service_name} service: {e}")
        return False

def check_all_services():
    """Check health of all required services"""
    health_status = {}
    for service, _ in SERVICES.items():
        health_status[service] = check_service_health(service, HEALTH_ENDPOINTS[service])
    return health_status

# Check if a package is installed
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Check required packages
required_packages = {
    "streamlit_drawable_canvas": "streamlit-drawable-canvas",
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
                sentences = json.load(f)
                logger.info(f"Loaded {len(sentences)} sample sentences")
                return sentences
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
    if not check_service_health("mangaocr", SERVICES["mangaocr"]):
        st.error("MangaOCR service is not available")
        return "Error: MangaOCR service is not available"
        
    try:
        # Convert to PIL Image if it's not already
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        temp_path = "temp_image.png"
        image.save(temp_path)
        with open(temp_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(SERVICES["mangaocr"], files=files, timeout=30)
        if Path(temp_path).exists():
            Path(temp_path).unlink()
        if response.status_code == 200:
            return response.json().get('text', '')
        else:
            logger.error(f"MangaOCR API error: {response.status_code} {response.text}")
            return "Error processing image"
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return "Error processing image"

# Translate Japanese text to English
def translate_text(text, prompts):
    if not check_service_health("llm", SERVICES["llm"]):
        st.error("LLM service is not available")
        return "Error: LLM service is not available"
        
    try:
        system_prompt = prompts['translation']['system']
        user_prompt = prompts['translation']['user'].format(text=text)

        response = requests.post(
            SERVICES["llm"],
            json={
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Translation not available")
    except Exception as e:
        logger.error(f"Translation error: {e}")

    return "Translation not available"

# Grade user response
def grade_response(target_sentence, submission, translation, prompts):
    if not check_service_health("llm", SERVICES["llm"]):
        st.error("LLM service is not available")
        return "Error: LLM service is not available"
        
    try:
        system_prompt = prompts['grading']['system']
        user_prompt = prompts['grading']['user'].format(
            target_sentence=target_sentence,
            submission=submission,
            translation=translation
        )

        response = requests.post(
            SERVICES["llm"],
            json={
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Grading not available")
    except Exception as e:
        logger.error(f"Grading error: {e}")

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

# Generate sentence using LLM service
def generate_sentence(category, word, prompts):
    if not check_service_health("llm", SERVICES["llm"]):
        st.error("LLM service is not available")
        return None
        
    try:
        system_prompt = prompts['sentence_generation']['system']
        user_prompt = prompts['sentence_generation']['user'].format(word=word)

        response = requests.post(
            SERVICES["llm"],
            json={
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            # Parse the response to extract Japanese and English parts
            if "Japanese:" in response_text and "English:" in response_text:
                japanese = response_text.split("Japanese:")[1].split("English:")[0].strip()
                english = response_text.split("English:")[1].strip()
                return {
                    "japanese": japanese,
                    "english": english,
                    "category": category,
                    "level": "N5"  # Default to N5 for now
                }
            else:
                logger.error(f"Invalid response format: {response_text}")
                return None
    except Exception as e:
        logger.error(f"Sentence generation error: {e}")
        return None

    return None

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

# Check service health and display status
health_status = check_all_services()

# Display service status
st.sidebar.title("Service Status")
for service, is_healthy in health_status.items():
    if is_healthy:
        st.sidebar.success(f"✅ {service}")
    else:
        st.sidebar.error(f"❌ {service}")

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
                                    st.error("Failed to generate a sentence. Please try again.")
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
