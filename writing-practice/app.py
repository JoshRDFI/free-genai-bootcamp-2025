import streamlit as st
import requests
from enum import Enum
import json
from typing import Optional, List, Dict
import logging
import random
import yaml
import os
from manga_ocr import MangaOcr
from PIL import Image
import io
import base64
from streamlit_drawable_canvas import st_canvas

# Setup Custom Logging ----
# Create a custom logger for your app only
logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to prevent duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

# Create file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - MY_APP - %(message)s')
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

class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initializing Japanese Learning App...")
        self.initialize_session_state()
        self.load_vocabulary()
        self.load_prompts()
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
        if 'n5_mode' not in st.session_state:
            st.session_state.n5_mode = True

    def load_prompts(self):
        """Load prompts from YAML file"""
        try:
            with open('prompts.yaml', 'r') as file:
                self.prompts = yaml.safe_load(file)
            logger.debug("Prompts loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            st.error(f"Failed to load prompts: {str(e)}")
            self.prompts = {
                "sentence_generation": {
                    "system": "You are a Japanese language teacher. Generate a natural Japanese sentence using the provided word. The sentence should use JLPT N5 level grammar and vocabulary only. Respond with ONLY the sentence, no explanations.",
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

    def load_vocabulary(self):
        """Fetch vocabulary from API using group_id from query parameters"""
        try:
            # Get group_id from query parameters
            group_id = st.query_params.get('group_id', '')

            if not group_id:
                st.error("No group_id provided in query parameters")
                self.vocabulary = None
                return

            # Make API request with the actual group_id
            url = f'http://localhost:5000/api/groups/{group_id}/words/raw'
            logger.debug(url)
            response = requests.get(url)
            logger.debug(f"Response status: {response.status_code}")

            # Check if response is successful and contains data
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Received data for group: {data.get('group_name', 'unknown')}")
                    self.vocabulary = data
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    st.error(f"Invalid JSON response from API: {response.text}")
                    self.vocabulary = None
            else:
                logger.error(f"API request failed: {response.status_code}")
                st.error(f"API request failed with status code: {response.status_code}")
                self.vocabulary = None
        except Exception as e:
            logger.error(f"Failed to load vocabulary: {e}")
            st.error(f"Failed to load vocabulary: {str(e)}")
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

    def generate_sentence(self, word: dict) -> str:
        """Generate a sentence using Ollama"""
        kanji = word.get('kanji', '')
        english = word.get('english', '')

        # Format the prompt using the template from prompts.yaml
        system_prompt = self.prompts["sentence_generation"]["system"]

        # Add N5 specific instructions
        user_prompt = self.prompts["sentence_generation"]["user"].format(word=kanji)
        if st.session_state.n5_mode:
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

        result = f"Japanese: {japanese}\nEnglish: {english}"
        logger.debug(f"Generated sentence: {result}")

        # Store the Japanese sentence separately for later use
        st.session_state.current_japanese = japanese

        return result

    def translate_text(self, text: str) -> str:
        """Translate Japanese text to English using Ollama"""
        system_prompt = self.prompts["translation"]["system"]
        user_prompt = self.prompts["translation"]["user"].format(text=text)

        logger.debug(f"Translating text: {text}")
        translation = self.call_ollama(user_prompt, system_prompt)
        logger.debug(f"Translation: {translation}")

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
            if st.session_state.n5_mode:
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

    def render_setup_state(self):
        """Render the setup state UI"""
        logger.debug("Entering render_setup_state")
        st.title("Japanese Writing Practice (JLPT N5)")

        if not self.vocabulary:
            logger.debug("No vocabulary loaded")
            st.warning("No vocabulary loaded. Please make sure a valid group_id is provided.")
            return

        # Display group name if available
        if self.vocabulary.get('group_name'):
            st.subheader(f"Group: {self.vocabulary['group_name']}")

        # Select evaluation level
        st.radio(
            "Select evaluation level:",
            [e.value for e in EvaluationLevel],
            key="evaluation_level_radio",
            on_change=lambda: setattr(st.session_state, 'evaluation_level',
                                     EvaluationLevel(st.session_state.evaluation_level_radio))
        )

        # Add key to button to ensure proper state management
        generate_button = st.button("Generate Sentence", key="generate_sentence_btn")
        logger.debug(f"Generate button state: {generate_button}")

        if generate_button:
            logger.info("Generate button clicked")
            st.session_state['last_click'] = 'generate_button'
            logger.debug(f"Session state after click: {st.session_state}")
            # Pick a random word from vocabulary
            if not self.vocabulary.get('words'):
                st.error("No words found in the vocabulary group")
                return

            word = random.choice(self.vocabulary['words'])
            logger.debug(f"Selected word: {word.get('english')} - {word.get('kanji')}")

            # Generate and display the sentence
            with st.spinner("Generating sentence..."):
                sentence = self.generate_sentence(word)
            st.markdown("### Generated Sentence")
            st.write(sentence)

            # Store the current sentence and move to practice state
            st.session_state.current_sentence = sentence
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

        st.write(f"English Sentence: {english_sentence}")

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

        elif input_method == InputMethod.WEBCAM:
            webcam_img = st.camera_input("Take a picture of your written Japanese")
            if webcam_img:
                image_data = webcam_img.getvalue()

        elif input_method == InputMethod.DRAW:
            # Drawing canvas
            st.write("Draw your Japanese characters below:")

            # Create a canvas component
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",  # Orange color with some transparency
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                height=300,
                width=600,
                drawing_mode="freedraw",
                key="canvas",
            )

            # If the canvas has data, convert it to an image
            if canvas_result.image_data is not None:
                # Convert the canvas data to a PIL Image
                img = Image.fromarray(canvas_result.image_data.astype('uint8'))

                # Convert to bytes
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                image_data = buf.getvalue()

                # Display the image
                st.image(img, caption="Your Drawing", use_column_width=True)

        submit_button = st.button("Submit for Review")
        if submit_button and image_data:
            with st.spinner("Processing your submission..."):
                st.session_state.review_data = self.grade_submission(image_data)
            st.session_state.app_state = AppState.REVIEW
            st.experimental_rerun()
        elif submit_button and not image_data:
            st.error("Please provide an image before submitting")

    def render_review_state(self):
        """Render the review state UI"""
        st.title("Review (JLPT N5)")

        # Extract and display the English part of the sentence
        english_sentence = ""
        for line in st.session_state.current_sentence.split('\n'):
            if line.startswith("English:"):
                english_sentence = line.replace("English:", "").strip()
                break

        st.write(f"English Sentence: {english_sentence}")
        st.write(f"Target Japanese: {st.session_state.current_japanese}")

        review_data = st.session_state.review_data
        st.subheader("Your Submission")
        st.write(f"Transcription: {review_data['transcription']}")
        st.write(f"Translation: {review_data['translation']}")

        # Display grade with color coding
        grade = review_data['grade']
        grade_color = {
            'S': 'green',
            'A': 'lightgreen',
            'B': 'orange',
            'C': 'red'
        }.get(grade, 'gray')

        st.markdown(f"Grade: <span style='color:{grade_color};font-weight:bold;'>{grade}</span>", unsafe_allow_html=True)
        st.write(f"Feedback: {review_data['feedback']}")

        if st.button("Next Question"):
            st.session_state.app_state = AppState.SETUP
            st.session_state.current_sentence = ""
            st.session_state.current_japanese = ""
            st.session_state.review_data = None
            st.experimental_rerun()

    def run(self):
        """Main app loop"""
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

# Run the app
if __name__ == "__main__":
    app = JapaneseLearningApp()
    app.run()