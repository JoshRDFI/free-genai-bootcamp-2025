# frontend/streamlit_app.py

import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import Optional

# Ensure the backend modules are accessible
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

# Add writing-practice to path
writing_practice_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'writing-practice'))
sys.path.insert(0, writing_practice_path)

# Import backend modules
from youtube.get_transcript import YouTubeTranscriptDownloader
from llm.question_generator import QuestionGenerator
from tts.audio_generator import AudioGenerator
from guardrails.rules import ContentGuardrails
from database.knowledge_base import KnowledgeBase

# Import writing practice modules
# Assuming these exist in your writing-practice/app.py
from writing_practice.vocabulary import VocabularyManager
from writing_practice.sentence_generator import SentenceGenerator

# Page config
st.set_page_config(
    page_title="JLPT Language Practice",
    page_icon="🎧",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'question_generator' not in st.session_state:
        st.session_state.question_generator = QuestionGenerator()
    if 'audio_generator' not in st.session_state:
        st.session_state.audio_generator = AudioGenerator()
    if 'transcript_downloader' not in st.session_state:
        st.session_state.transcript_downloader = YouTubeTranscriptDownloader()
    if 'guardrails' not in st.session_state:
        st.session_state.guardrails = ContentGuardrails()
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = KnowledgeBase()
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'current_practice_type' not in st.session_state:
        st.session_state.current_practice_type = None
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
    if 'current_transcript' not in st.session_state:
        st.session_state.current_transcript = None
    # Initialize writing practice components
    if 'vocabulary_manager' not in st.session_state:
        st.session_state.vocabulary_manager = VocabularyManager()
    if 'sentence_generator' not in st.session_state:
        st.session_state.sentence_generator = SentenceGenerator()

# [Keep your existing functions: load_stored_questions, process_youtube_url,
#  render_youtube_input, render_interactive_practice, render_sidebar, render_rag_visualization]

def render_writing_practice():
    """Render the writing practice section"""
    st.subheader("Writing Practice")

    # Category selection
    categories = ["Basic Greetings", "Food & Dining", "Travel Phrases", "Daily Activities", "Numbers & Time"]
    selected_category = st.selectbox("Select Vocabulary Category", categories)

    # Get vocabulary for selected category
    vocabulary = st.session_state.vocabulary_manager.get_vocabulary(selected_category.lower().replace(" & ", "_").replace(" ", "_"))

    # Display vocabulary section
    with st.expander("Vocabulary List", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Kanji**")
            for word in vocabulary:
                st.write(word["kanji"])
        with col2:
            st.write("**Romaji**")
            for word in vocabulary:
                st.write(word["romaji"])
        with col3:
            st.write("**English**")
            for word in vocabulary:
                st.write(word["english"])

    # Practice section
    st.subheader("Practice Writing")
    practice_type = st.radio("Select Practice Type", ["Sentence Completion", "Translation Exercise"])

    if practice_type == "Sentence Completion":
        # Sentence completion exercise
        if "current_sentence" not in st.session_state:
            st.session_state.current_sentence = st.session_state.sentence_generator.generate_sentence(selected_category)

        sentence = st.session_state.current_sentence
        blank_word = sentence["blank_word"]
        sentence_with_blank = sentence["sentence_with_blank"]

        st.write(f"**Complete the sentence by filling in the blank:**")
        st.write(sentence_with_blank)

        user_answer = st.text_input("Your answer:")

        if st.button("Check Answer"):
            if user_answer.lower() == blank_word["romaji"].lower():
                st.success(f"Correct! '{blank_word['kanji']}' ({blank_word['romaji']}) means '{blank_word['english']}'")
            else:
                st.error(f"Not quite. The correct answer is '{blank_word['kanji']}' ({blank_word['romaji']})")

        if st.button("New Sentence"):
            st.session_state.current_sentence = st.session_state.sentence_generator.generate_sentence(selected_category)
            st.experimental_rerun()

    else:  # Translation Exercise
        if "current_translation" not in st.session_state:
            st.session_state.current_translation = st.session_state.sentence_generator.generate_translation_exercise(selected_category)

        translation = st.session_state.current_translation
        japanese_sentence = translation["japanese"]
        english_translation = translation["english"]

        st.write(f"**Translate the following sentence to English:**")
        st.write(japanese_sentence)

        user_translation = st.text_area("Your translation:")

        if st.button("Check Translation"):
            # Simple check - in a real app you'd want more sophisticated comparison
            similarity = st.session_state.sentence_generator.check_translation_similarity(
                user_translation, english_translation
            )
            if similarity > 0.7:
                st.success(f"Good translation! Reference: '{english_translation}'")
            else:
                st.warning(f"Your translation differs from the reference. Consider: '{english_translation}'")

        if st.button("New Translation"):
            st.session_state.current_translation = st.session_state.sentence_generator.generate_translation_exercise(selected_category)
            st.experimental_rerun()

def main():
    st.title("JLPT Language Practice")
    initialize_session_state()
    render_sidebar()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Process YouTube Video",
        "Practice Questions",
        "RAG Visualization",
        "Writing Practice"
    ])

    with tab1:
        render_youtube_input()
    with tab2:
        render_interactive_practice()
    with tab3:
        render_rag_visualization()
    with tab4:
        render_writing_practice()

if __name__ == "__main__":
    main()