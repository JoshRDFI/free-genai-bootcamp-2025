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
    page_title="Listening - Speaking Practice",
    page_icon="🎧",
    layout="wide"
)

# Add custom CSS for background image
def add_background_image():
    background_image_path = os.path.join(project_root, "..", "images", "spring_shrine.png")
    st.markdown(
        f"""
        <style>
        /* Apply background to the entire app including sidebar */
        .stApp {{
            background-image: url("data:image/png;base64,{get_base64_of_bin_file(background_image_path)}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        
        /* Style the sidebar with more transparent background */
        .css-1d391kg {{
            background-color: rgba(255, 255, 255, 0.2) !important;
            backdrop-filter: blur(1px);
            border-right: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Style the main content area */
        .stApp > main {{
            background-color: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(5px);
        }}
        
        /* Style the header with more transparency */
        .stApp > header {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(1px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Remove the white bar at the top */
        .stApp > header > div {{
            background: transparent !important;
        }}
        
        /* Style cards and containers for better visibility */
        .stCard {{
            background-color: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        
        /* Style buttons with better colors */
        .stButton > button {{
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
        }}
        
        .stButton > button:hover {{
            background-color: #45a049 !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }}
        
        /* Style selectboxes */
        .stSelectbox > div > div {{
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Fix dropdown text color */
        .stSelectbox > div > div > div {{
            color: #000000 !important;
        }}
        
        .stSelectbox > div > div > div > div {{
            color: #000000 !important;
        }}
        
        /* Fix dropdown options text color */
        .stSelectbox [data-baseweb="select"] {{
            color: #000000 !important;
        }}
        
        .stSelectbox [data-baseweb="select"] > div {{
            color: #000000 !important;
        }}
        
        /* Style text inputs */
        .stTextInput > div > div > input {{
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            color: #000000 !important;
        }}
        
        /* Style radio buttons */
        .stRadio > div {{
            background-color: rgba(255, 255, 255, 0.7) !important;
            padding: 10px !important;
            border-radius: 8px !important;
        }}
        
        /* Fix radio button text color */
        .stRadio > div > div {{
            color: #000000 !important;
        }}
        
        .stRadio > div > div > div {{
            color: #000000 !important;
        }}
        
        .stRadio > div > div > div > div {{
            color: #000000 !important;
        }}
        
        /* Fix radio button labels */
        .stRadio > div > div > div > div > label {{
            color: #000000 !important;
        }}
        
        /* Fix radio button text in format_func */
        .stRadio > div > div > div > div > label > div {{
            color: #000000 !important;
        }}
        
        /* Additional radio button text fixes */
        .stRadio [data-baseweb="radio"] {{
            color: #000000 !important;
        }}
        
        .stRadio [data-baseweb="radio"] > div {{
            color: #000000 !important;
        }}
        
        .stRadio [data-baseweb="radio"] > div > div {{
            color: #000000 !important;
        }}
        
        /* Style expanders */
        .streamlit-expanderHeader {{
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Style tabs - make completely transparent */
        .stTabs {{
            background: transparent !important;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            background: transparent !important;
            border-radius: 8px 8px 0 0 !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            border-radius: 8px 8px 0 0 !important;
            color: #000000 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: transparent !important;
            color: #000000 !important;
        }}
        
        /* Make tab content container transparent */
        .stTabs [data-baseweb="tab-panel"] {{
            background: transparent !important;
        }}
        
        /* Fix any tab container backgrounds */
        .stTabs > div {{
            background: transparent !important;
        }}
        
        .stTabs > div > div {{
            background: transparent !important;
        }}
        
        /* Hide Streamlit's default background */
        .main .block-container {{
            background: transparent !important;
        }}
        
        /* Ensure sidebar background is properly applied with more transparency */
        section[data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.2) !important;
            backdrop-filter: blur(1px);
        }}
        
        /* Additional header transparency fixes */
        .stApp > header > div > div {{
            background: transparent !important;
        }}
        
        /* Fix any remaining white bars */
        .stApp > header > div > div > div {{
            background: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def get_base64_of_bin_file(bin_file):
    import base64
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
                                    if 'category' in questions[0]:
                                        st.write(f"**Category:** {questions[0]['category']}")
                                    st.write("**Question:**")
                                    st.write(questions[0]['question'])
                                    st.write("**Options:**")
                                    for i, option in enumerate(questions[0]['options'], 1):
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
    
    # Load stored questions and filter by selected topic and practice type
    stored_questions = load_stored_questions()
    filtered_questions = []
    
    for qid, qdata in stored_questions.items():
        if qdata.get('practice_type') == practice_type and qdata.get('topic') == topic:
            filtered_questions.append((qid, qdata))
    
    if not filtered_questions:
        st.info(f"No questions available for {practice_type} - {topic}. Please process a video or generate questions first.")
        return
    
    # Select a random question from the filtered list
    import random
    if 'current_topic_question_index' not in st.session_state:
        st.session_state.current_topic_question_index = 0
    
    # Update question index if topic/practice type changed
    topic_key = f"{practice_type}_{topic}"
    if 'last_topic_key' not in st.session_state or st.session_state.last_topic_key != topic_key:
        st.session_state.current_topic_question_index = 0
        st.session_state.last_topic_key = topic_key
    
    # Get current question
    current_qid, current_qdata = filtered_questions[st.session_state.current_topic_question_index]
    current_question = current_qdata['question']
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if 'category' in current_question:
            st.write(f"**Category:** {current_question['category']}")
        st.write("**Question:**")
        st.write(current_question['question'])

        # Display the image if available - check both old image_path and new images structure
        image_path = current_question.get('image_path')
        images = current_question.get('images', {})
        
        if image_path and os.path.exists(image_path):
            st.image(image_path, caption="Select the correct option.")
        elif images:
            # Display all available images from the images dictionary
            st.write("**Visual Options:**")
            
            # Construct full path to images directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            images_dir = os.path.join(project_root, "backend", "data", "images")
            
            # Create columns for displaying images
            image_cols = st.columns(len(images))
            
            for i, (option_letter, image_filename) in enumerate(images.items()):
                full_image_path = os.path.join(images_dir, image_filename)
                
                with image_cols[i]:
                    if os.path.exists(full_image_path):
                        st.image(full_image_path, caption=f"Option {option_letter}", use_container_width=True)
                    else:
                        st.info(f"Image {option_letter} not found: {full_image_path}")
        else:
            st.info("No image available for this question.")

        options = current_question['options']
        selected = st.radio(
            "Choose your answer:",
            options,
            format_func=lambda x: f"{options.index(x) + 1}. {x}"
        )
        if selected and st.button("Submit Answer"):
            selected_index = options.index(selected) + 1
            st.session_state.feedback = st.session_state.question_generator.get_feedback(
                current_question,
                selected_index
            )
            st.rerun()
        
        # Navigation buttons for questions within the same topic
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("Previous Question") and st.session_state.current_topic_question_index > 0:
                st.session_state.current_topic_question_index -= 1
                st.rerun()
        with col_nav2:
            if st.button("Next Question") and st.session_state.current_topic_question_index < len(filtered_questions) - 1:
                st.session_state.current_topic_question_index += 1
                st.rerun()
        
        # Show question counter
        st.write(f"Question {st.session_state.current_topic_question_index + 1} of {len(filtered_questions)} for {topic}")
        
    with col2:
        st.write("**Audio Controls**")
        current_audio = current_qdata.get('audio_file')
        
        if current_audio:
            st.audio(current_audio)
        elif current_question:
            if st.button("Generate Audio"):
                with st.spinner("Generating audio..."):
                    question_text = current_question['question']
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Use absolute path to ensure correct directory
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(current_dir)
                    output_file = os.path.join(project_root, "backend", "data", "audio", f"question_{timestamp}.mp3")
                    print(f"Generating audio for question: {question_text}")
                    print(f"Output file path: {output_file}")
                    audio_file = st.session_state.audio_generator.generate_audio(
                        question_text,
                        output_file
                    )
                    if audio_file:
                        print(f"Audio file generated: {audio_file}")
                        print(f"File exists: {os.path.exists(audio_file)}")
                        # Update the stored question with audio file
                        current_qdata['audio_file'] = audio_file
                        # Save updated questions
                        stored_questions[current_qid] = current_qdata
                        questions_file = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "backend", "data", "stored_questions.json"
                        )
                        with open(questions_file, 'w', encoding='utf-8') as f:
                            json.dump(stored_questions, f, ensure_ascii=False, indent=2)
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
        if st.button("Generate Any Missing Images"):
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
    add_background_image()
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