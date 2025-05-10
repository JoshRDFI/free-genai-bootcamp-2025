"""
UI components for Japanese text input methods.
"""
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
import tempfile
from ...core.ocr import get_ocr_processor
from ...utils.logging import get_logger

logger = get_logger(__name__)

class InputMethodHandler:
    """Handles different methods of Japanese text input."""
    
    def __init__(self):
        """Initialize the input method handler."""
        self.ocr_processor = get_ocr_processor()
    
    def render_canvas_input(self) -> Optional[str]:
        """
        Render the drawing canvas for handwritten input.
        
        Returns:
            Extracted text from the canvas or None if no input
        """
        try:
            # Canvas settings
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.3)",
                stroke_width=2,
                stroke_color="#000000",
                background_color="#ffffff",
                height=200,
                drawing_mode="freedraw",
                key="canvas"
            )
            
            if canvas_result.json_data is not None:
                # Convert canvas to image
                if canvas_result.image_data is not None:
                    # Convert to PIL Image
                    img = Image.fromarray(canvas_result.image_data)
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        img.save(tmp.name)
                        # Process with OCR
                        text = self.ocr_processor.process_image(tmp.name)
                        Path(tmp.name).unlink()
                        return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error in canvas input: {e}")
            st.error("Error processing canvas input")
            return None
    
    def handle_file_upload(self) -> Optional[str]:
        """
        Handle uploaded image file.
        
        Returns:
            Extracted text from the image or None if no input
        """
        try:
            uploaded_file = st.file_uploader(
                "Upload an image of Japanese text",
                type=["png", "jpg", "jpeg"]
            )
            
            if uploaded_file is not None:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    # Process with OCR
                    text = self.ocr_processor.process_image(tmp.name)
                    Path(tmp.name).unlink()
                    return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error in file upload: {e}")
            st.error("Error processing uploaded file")
            return None
    
    def handle_webcam_input(self) -> Optional[str]:
        """
        Handle webcam input for capturing Japanese text.
        
        Returns:
            Extracted text from the webcam image or None if no input
        """
        try:
            # Webcam input
            img_file_buffer = st.camera_input("Take a picture of Japanese text")
            
            if img_file_buffer is not None:
                # Convert to PIL Image
                img = Image.open(img_file_buffer)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img.save(tmp.name)
                    # Process with OCR
                    text = self.ocr_processor.process_image(tmp.name)
                    Path(tmp.name).unlink()
                    return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error in webcam input: {e}")
            st.error("Error processing webcam input")
            return None
    
    def render_input_methods(self) -> Optional[str]:
        """
        Render all input methods and handle user selection.
        
        Returns:
            Extracted text from the selected input method or None
        """
        input_method = st.radio(
            "Choose input method:",
            ["Draw", "Upload Image", "Webcam"],
            horizontal=True
        )
        
        if input_method == "Draw":
            return self.render_canvas_input()
        elif input_method == "Upload Image":
            return self.handle_file_upload()
        else:  # Webcam
            return self.handle_webcam_input()

# Create singleton instance
_input_handler = None

def get_input_handler() -> InputMethodHandler:
    """Get the singleton input handler instance."""
    global _input_handler
    if _input_handler is None:
        _input_handler = InputMethodHandler()
    return _input_handler 