"""
Main page for the Japanese writing practice application.
"""
import streamlit as st
from ..components.input_methods import get_input_handler
from ...core.translation import get_translator
from ...core.grading import get_grader
from ...utils.logging import get_logger
from ...utils.config import get_config

logger = get_logger(__name__)

def render_header():
    """Render the application header."""
    st.title("Japanese Writing Practice")
    st.markdown("""
    Practice writing Japanese characters and get instant feedback.
    Choose your preferred input method below.
    """)

def render_input_section():
    """Render the input section with all available methods."""
    st.header("Input")
    input_handler = get_input_handler()
    return input_handler.render_input_methods()

def render_translation_section(input_text: str):
    """Render the translation section."""
    if not input_text:
        return
    
    st.header("Translation")
    translator = get_translator()
    translation = translator.translate(input_text)
    
    if translation:
        st.write("English translation:")
        st.write(translation)

def render_grading_section(input_text: str, target_text: str):
    """Render the grading section."""
    if not input_text or not target_text:
        return
    
    st.header("Grading")
    grader = get_grader()
    grade_result = grader.grade(input_text, target_text)
    
    if grade_result:
        st.write("Grade:", grade_result['grade'])
        st.write("Feedback:", grade_result['feedback'])

def render_main_page():
    """Render the main application page."""
    try:
        # Initialize session state
        if 'target_text' not in st.session_state:
            st.session_state.target_text = None
        
        # Render header
        render_header()
        
        # Get input text
        input_text = render_input_section()
        
        # If we have input, process it
        if input_text:
            st.write("Detected text:", input_text)
            
            # Translation
            render_translation_section(input_text)
            
            # Grading (if target text exists)
            if st.session_state.target_text:
                render_grading_section(input_text, st.session_state.target_text)
            
            # Option to set as target text
            if st.button("Set as target text"):
                st.session_state.target_text = input_text
                st.success("Target text set!")
        
        # Display current target text
        if st.session_state.target_text:
            st.sidebar.header("Current Target")
            st.sidebar.write(st.session_state.target_text)
            
            if st.sidebar.button("Clear Target"):
                st.session_state.target_text = None
                st.sidebar.success("Target cleared!")
        
    except Exception as e:
        logger.error(f"Error in main page: {e}")
        st.error("An error occurred. Please try again.")

def main():
    """Main entry point for the application."""
    render_main_page() 