import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.youtube.get_transcript import YouTubeTranscriptDownloader
from backend.llm.question_generator import QuestionGenerator
from backend.tts.audio_generator import AudioGenerator
from backend.guardrails.rules import ContentGuardrails

# Page config
st.set_page_config(
    page_title="JLPT Listening Practice",
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

def load_stored_questions():
    """Load previously stored questions from JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def process_youtube_url(url: str) -> Optional[str]:
    """Process YouTube URL and return transcript"""
    try:
        # Get transcript
        transcript = st.session_state.transcript_downloader.get_transcript(url)
        if not transcript:
            st.error("Failed to download transcript")
            return None

        # Extract video ID
        video_id = st.session_state.transcript_downloader.extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL")
            return None

        # Save transcript
        transcript_text = "\n".join(item["text"] for item in transcript)

        # Validate content
        is_valid, reason = st.session_state.guardrails.validate_transcript(transcript_text)
        if not is_valid:
            st.error(f"Content validation failed: {reason}")
            return None

        # Save transcript to file
        st.session_state.transcript_downloader.save_transcript(transcript, video_id)
        return transcript_text

    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        return None

def render_youtube_input():
    """Render YouTube URL input section"""
    st.subheader("Process YouTube Video")

    # YouTube URL input
    youtube_url = st.text_input(
        "Enter YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=..."
    )

    if youtube_url:
        if st.button("Process Video"):
            with st.spinner("Processing video..."):
                transcript = process_youtube_url(youtube_url)
                if transcript:
                    st.session_state.current_transcript = transcript
                    st.success("Video processed successfully!")

                    # Show transcript preview
                    with st.expander("Show Transcript"):
                        st.text_area("Transcript", transcript, height=200)

                    # Generate questions button
                    if st.button("Generate Questions from Transcript"):
                        with st.spinner("Generating questions..."):
                            # TODO: Implement question generation from transcript
                            st.info("Question generation from transcript will be implemented soon!")

def render_interactive_practice():
    """Render the interactive practice section"""
    st.subheader("Practice Questions")

    # Practice type selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Phrase Matching"]
    )

    # Topic selection
    topics = {
        "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
        "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
    }

    topic = st.selectbox(
        "Select Topic",
        topics[practice_type]
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.session_state.current_question:
            # Display current question
            st.write("**Introduction:**")
            st.write(st.session_state.current_question['Introduction'])
            st.write("**Conversation:**")
            st.write(st.session_state.current_question['Conversation'])
            st.write("**Question:**")
            st.write(st.session_state.current_question['Question'])

            # Display options and handle answers
            options = st.session_state.current_question['Options']
            selected = st.radio(
                "Choose your answer:",
                options,
                index=None,
                format_func=lambda x: f"{options.index(x) + 1}. {x}"
            )

            if selected and st.button("Submit Answer"):
                selected_index = options.index(selected) + 1
                st.session_state.feedback = st.session_state.question_generator.get_feedback(
                    st.session_state.current_question,
                    selected_index
                )
                st.rerun()

    with col2:
        # Audio controls
        st.write("**Audio Controls**")
        if st.session_state.current_audio:
            st.audio(st.session_state.current_audio)
        elif st.session_state.current_question:
            if st.button("Generate Audio"):
                with st.spinner("Generating audio..."):
                    audio_file = st.session_state.audio_generator.generate_audio(
                        st.session_state.current_question
                    )
                    if audio_file:
                        st.session_state.current_audio = audio_file
                        st.rerun()

def render_sidebar():
    """Render sidebar with saved questions"""
    with st.sidebar:
        st.header("Saved Questions")
        stored_questions = load_stored_questions()

        if stored_questions:
            for qid, qdata in stored_questions.items():
                button_label = f"{qdata['practice_type']} - {qdata['topic']}\n{qdata['created_at']}"
                if st.button(button_label, key=qid):
                    st.session_state.current_question = qdata['question']
                    st.session_state.current_practice_type = qdata['practice_type']
                    st.session_state.current_topic = qdata['topic']
                    st.session_state.current_audio = qdata.get('audio_file')
                    st.session_state.feedback = None
                    st.rerun()
        else:
            st.info("No saved questions yet. Process a video or generate questions to see them here!")

def main():
    st.title("JLPT Listening Practice")

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Process YouTube Video", "Practice Questions"])

    with tab1:
        render_youtube_input()

    with tab2:
        render_interactive_practice()

if __name__ == "__main__":
    main()