# frontend/streamlit_app.py

import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import Optional

# Fix path configuration - use relative path from current file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_dir = os.path.join(project_root, "backend")
sys.path.insert(0, project_root)

# Import backend modules
from backend.youtube.get_transcript import YouTubeTranscriptDownloader
from backend.llm.question_generator import QuestionGenerator
from backend.tts.audio_generator import AudioGenerator
from backend.guardrails.rules import ContentGuardrails
from backend.database.knowledge_base import KnowledgeBase

# Create necessary directories
os.makedirs(os.path.join(project_root, "backend", "data", "questions"), exist_ok=True)
os.makedirs(os.path.join(project_root, "backend", "data", "transcripts"), exist_ok=True)
os.makedirs(os.path.join(project_root, "backend", "data", "images"), exist_ok=True)
os.makedirs(os.path.join(project_root, "backend", "data", "audio"), exist_ok=True)
os.makedirs(os.path.join(project_root, "backend", "logs"), exist_ok=True)

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

def load_stored_questions():
    """Load previously stored questions from JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend", "data", "stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def process_youtube_url(url: str) -> Optional[str]:
    """Process YouTube URL and return transcript"""
    try:
        transcript = st.session_state.transcript_downloader.get_transcript(url)
        if not transcript:
            st.error("Failed to download transcript")
            return None

        video_id = st.session_state.transcript_downloader.extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL")
            return None

        transcript_text = "\n".join(item["text"] for item in transcript)
        is_valid, reason = st.session_state.guardrails.validate_transcript(transcript_text)
        if not is_valid:
            st.error(f"Content validation failed: {reason}")
            return None

        st.session_state.transcript_downloader.save_transcript(transcript, video_id)
        # Also save into the knowledge base (which now saves to ChromaDB and SQLite)
        st.session_state.knowledge_base.save_transcript(video_id, transcript_text)
        return transcript_text
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        return None

def render_youtube_input():
    """Render YouTube URL input section"""
    st.subheader("Process YouTube Video")
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
                    with st.expander("Show Transcript"):
                        st.text_area("Transcript", transcript, height=200)
                    if st.button("Generate Questions from Transcript"):
                        with st.spinner("Generating questions..."):
                            try:
                                video_id = st.session_state.transcript_downloader.extract_video_id(youtube_url)
                                if not video_id:
                                    st.error("Failed to extract video ID from URL")
                                    return

                                # Log the start of question generation
                                print(f"Starting question generation for video {video_id}")
                                
                                # Convert transcript text to list of dicts format expected by generate_questions
                                transcript_items = [{"text": line} for line in transcript.split("\n") if line.strip()]
                                
                                if not transcript_items:
                                    st.error("No valid transcript lines found")
                                    return
                                
                                print(f"Processing {len(transcript_items)} transcript lines")
                                
                                # Create a placeholder for progress updates
                                status_placeholder = st.empty()
                                status_placeholder.text("Connecting to LLM service...")
                                
                                try:
                                    questions = st.session_state.question_generator.generate_questions(
                                        transcript_items,
                                        video_id,
                                        num_questions=3
                                    )
                                    
                                    # Store all questions in session state
                                    st.session_state.generated_questions = questions
                                    st.session_state.current_question = questions[0]  # Show first question
                                    status_placeholder.success(f"Generated {len(questions)} questions!")
                                    
                                    # Display the first question
                                    st.write("**Question 1:**")
                                    st.write("**Introduction:**")
                                    st.write(questions[0]['Introduction'])
                                    st.write("**Conversation:**")
                                    st.write(questions[0]['Conversation'])
                                    st.write("**Question:**")
                                    st.write(questions[0]['Question'])
                                    st.write("**Options:**")
                                    for i, option in enumerate(questions[0]['Options'], 1):
                                        st.write(f"{i}. {option}")
                                    
                                    # Add navigation buttons for questions
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if len(questions) > 1:
                                            if st.button("Next Question"):
                                                current_index = questions.index(st.session_state.current_question)
                                                st.session_state.current_question = questions[(current_index + 1) % len(questions)]
                                                st.rerun()
                                    with col2:
                                        if st.button("Previous Question"):
                                            current_index = questions.index(st.session_state.current_question)
                                            st.session_state.current_question = questions[(current_index - 1) % len(questions)]
                                            st.rerun()
                                            
                                except TimeoutError:
                                    status_placeholder.error("LLM service timed out. Please try again.")
                                    print("LLM service request timed out")
                                except ConnectionError:
                                    status_placeholder.error("Could not connect to LLM service. Please check if the service is running.")
                                    print("Failed to connect to LLM service")
                                except ValueError as e:
                                    status_placeholder.error(f"Invalid response from LLM service: {str(e)}")
                                    print(f"LLM service validation error: {str(e)}")
                                except RuntimeError as e:
                                    status_placeholder.error(f"Error generating questions: {str(e)}")
                                    print(f"Question generation error: {str(e)}")
                                except Exception as e:
                                    status_placeholder.error(f"An unexpected error occurred: {str(e)}")
                                    print(f"Unexpected error: {str(e)}")
                                    
                            except Exception as e:
                                print(f"Error during question generation: {str(e)}")
                                st.error(f"An error occurred: {str(e)}")

def render_interactive_practice():
    """Render the interactive practice section"""
    st.subheader("Practice Questions")
    practice_type = st.selectbox("Select Practice Type", ["Dialogue Practice", "Phrase Matching"])
    topics = {
        "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
        "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
    }
    topic = st.selectbox("Select Topic", topics[practice_type])
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.current_question:
            st.write("**Introduction:**")
            st.write(st.session_state.current_question['Introduction'])
            st.write("**Conversation:**")
            st.write(st.session_state.current_question['Conversation'])
            st.write("**Question:**")
            st.write(st.session_state.current_question['Question'])

            # Display the image if available
            image_path = st.session_state.current_question.get('image_path')
            if image_path:
                st.image(image_path, caption="Select the correct option.")
            else:
                st.info("No image available for this question.")

            options = st.session_state.current_question['Options']
            selected = st.radio(
                "Choose your answer:",
                options,
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
        st.write("**Audio Controls**")
        if st.session_state.current_audio:
            st.audio(st.session_state.current_audio)
        elif st.session_state.current_question:
            if st.button("Generate Audio"):
                with st.spinner("Generating audio..."):
                    question_text = st.session_state.current_question['Question']
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = os.path.join("backend", "data", "audio", f"question_{timestamp}.mp3")
                    print(f"Generating audio for question: {question_text}")
                    print(f"Output file path: {output_file}")
                    audio_file = st.session_state.audio_generator.generate_audio(
                        question_text,
                        output_file
                    )
                    if audio_file:
                        print(f"Audio file generated: {audio_file}")
                        print(f"File exists: {os.path.exists(audio_file)}")
                        st.session_state.current_audio = audio_file
                        st.rerun()
                    else:
                        print("Audio generation failed.")

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
        # Add button to generate images for old questions
        if st.button("Generate Images for Old Questions"):
            with st.spinner("Generating images for old questions..."):
                st.session_state.question_generator.generate_image_for_old_questions()
                st.success("Images generated for old questions!")

def render_rag_visualization():
    """New tab: Visualize the RAG process via similarity queries"""
    st.subheader("RAG Visualization: Embedding Similarity")
    query = st.text_input("Enter a query to find similar transcripts:", "")
    if st.button("Find Similar Transcripts"):
        if query:
            kb = st.session_state.knowledge_base
            results = kb.find_similar_transcripts(query)
            st.write("Similarity Results:")
            # Display the results nicely
            if results and "documents" in results:
                docs = results["documents"][0]
                distances = results.get("distances", [[]])[0]
                # Results are returned as a list of documents and their similarity scores
                for i, doc in enumerate(docs):
                    st.markdown(f"**Result {i+1}:**")
                    st.write(f"Text: {doc}")
                    st.write(f"Distance: {distances[i]}")
            else:
                st.info("No similar transcripts found.")
        else:
            st.error("Please enter a query.")

def main():
    st.title("JLPT Listening Practice")
    initialize_session_state()
    render_sidebar()
    tab1, tab2, tab3 = st.tabs(["Process YouTube Video", "Practice Questions", "RAG Visualization"])
    with tab1:
        render_youtube_input()
    with tab2:
        render_interactive_practice()
    with tab3:
        render_rag_visualization()

if __name__ == "__main__":
    main()