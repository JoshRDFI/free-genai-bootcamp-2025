# API communication module for Japanese Learning Visual Novel
# This module provides direct access to opea-docker services

import requests
import json
import os
import base64
from io import BytesIO

# API endpoints configuration
# Direct access to opea-docker services
# Use localhost when running the game locally, or the Docker service name when running in Docker

# Game server API base URL for game-specific endpoints
GAME_API_BASE_URL = os.environ.get('GAME_API_BASE_URL', 'http://localhost:8080/api')

# Direct service endpoints
OLLAMA_SERVER_URL = os.environ.get('OLLAMA_SERVER_URL', 'http://localhost:8008')
LLM_TEXT_ENDPOINT = os.environ.get('LLM_TEXT_URL', 'http://localhost:9000/v1/chat/completions')
GUARDRAILS_URL = os.environ.get('GUARDRAILS_URL', 'http://localhost:9400/v1/guardrails')
CHROMADB_URL = os.environ.get('CHROMADB_URL', 'http://localhost:8050')
TTS_ENDPOINT = os.environ.get('TTS_URL', 'http://localhost:9200/tts')
ASR_ENDPOINT = os.environ.get('ASR_URL', 'http://localhost:9300/asr')
LLM_VISION_ENDPOINT = os.environ.get('LLM_VISION_URL', 'http://localhost:9101/v1/vision')
IMAGE_GEN_ENDPOINT = os.environ.get('WAIFU_DIFFUSION_URL', 'http://localhost:9500')
EMBEDDINGS_ENDPOINT = os.environ.get('EMBEDDINGS_URL', 'http://localhost:6000/embed')
DATABASE_ENDPOINT = f"{GAME_API_BASE_URL}/database"

class APIService:
    """Centralized API service for all external calls"""
    
    @staticmethod
    def save_progress(user_id, lesson_id, scene_id, completed=False):
        """Save player progress to the server"""
        try:
            response = requests.post(
                f"{GAME_API_BASE_URL}/progress",
                json={
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "scene_id": scene_id,
                    "completed": completed
                }
            )
            return response.json()
        except Exception as e:
            print(f"Failed to save progress: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_translation(text, source_lang="ja", target_lang="en"):
        """Get translation for text using LLM service"""
        try:
            response = requests.post(
                LLM_TEXT_ENDPOINT,
                json={
                    "text": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                }
            )
            result = response.json()
            return result.get("text", "Translation failed")
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return "Translation failed"
    
    @staticmethod
    def get_audio(text, voice="ja-JP"):
        """Get audio for text using TTS service"""
        try:
            response = requests.post(
                TTS_ENDPOINT,
                json={
                    "text": text,
                    "voice": voice
                }
            )
            result = response.json()
            audio_path = result.get("audio_path")
            if audio_path:
                return audio_path
            return None
        except Exception as e:
            print(f"TTS failed: {str(e)}")
            return None
    
    @staticmethod
    def speech_to_text(audio_path, language="ja-JP"):
        """Convert speech to text using ASR service"""
        try:
            with open(audio_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
                
            response = requests.post(
                ASR_ENDPOINT,
                json={
                    "audio_data": audio_data,
                    "language": language
                }
            )
            result = response.json()
            return result.get("text", "")
        except Exception as e:
            print(f"ASR failed: {str(e)}")
            return ""
    @staticmethod
    def add_vocabulary(user_id, japanese, reading=None, english=None, lesson_id=None):
        """Add vocabulary to player's list"""
        try:
            response = requests.post(
                f"{GAME_API_BASE_URL}/vocabulary",
                json={
                    "user_id": user_id,
                    "japanese": japanese,
                    "reading": reading,
                    "english": english,
                    "lesson_id": lesson_id
                }
            )
            return response.json()
        except Exception as e:
            print(f"Failed to add vocabulary: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_image(prompt, image_type="background", negative_prompt=None, 
                      width=512, height=512, style="anime"):
        """Generate an image using the image generation service
        
        Args:
            prompt: The text prompt for image generation
            image_type: Either 'background' or 'character' to determine save location
            negative_prompt: What to avoid in the image
            width: Image width
            height: Image height
            style: Image style (anime, realistic, etc.)
            
        Returns:
            Path to the generated image or None if generation failed
        """
        try:
            response = requests.post(
                f"{IMAGE_GEN_ENDPOINT}",
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "style": style,
                    "return_format": "base64"
                }
            )
            
            if response.status_code != 200:
                print(f"Image generation failed: {response.text}")
                return None
                
            result = response.json()
            
            if "image" in result:
                # Save the base64 image to a file
                image_data = base64.b64decode(result["image"])
                
                # Determine the save directory based on image_type
                if image_type.lower() == "character":
                    save_dir = "images/characters"
                else:  # Default to backgrounds
                    save_dir = "images/backgrounds"
                
                # Create directory if it doesn't exist
                os.makedirs(save_dir, exist_ok=True)
                
                # Create a safe filename from the prompt
                safe_filename = "".join(c for c in prompt if c.isalnum() or c in " _-").strip()
                safe_filename = safe_filename.replace(" ", "_")[:30]
                
                # Save the image
                image_path = f"{save_dir}/{safe_filename}.png"
                
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                # Log the saved image
                print(f"Generated image saved to: {image_path}")
                
                return image_path
            else:
                print("Image generation failed: No image data received")
                return None
        except Exception as e:
            print(f"Image generation failed: {str(e)}")
            return None
            
    @staticmethod
    def generate_conversation(context, characters, grammar_points=None, vocabulary=None, num_exchanges=3):
        """Generate a dynamic conversation using the LLM"""
        try:
            if grammar_points is None:
                grammar_points = []
            if vocabulary is None:
                vocabulary = []
                
            response = requests.post(
                f"{LLM_TEXT_ENDPOINT}/generate-conversation",
                json={
                    "context": context,
                    "characters": characters,
                    "grammar_points": grammar_points,
                    "vocabulary": vocabulary,
                    "num_exchanges": num_exchanges,
                    "include_translations": True
                }
            )
            
            if response.status_code != 200:
                print(f"Conversation generation failed: {response.text}")
                return None
                
            result = response.json()
            
            # Check if we got a valid conversation structure
            if "conversation" in result:
                return result["conversation"]
            elif "error" in result:
                print(f"Conversation generation error: {result['error']}")
                return None
            else:
                print("Unexpected response format from conversation generator")
                return None
        except Exception as e:
            print(f"Failed to generate conversation: {str(e)}")
            return None
            
    @staticmethod
    def generate_lesson(topic, grammar_points=None, vocabulary_focus=None, lesson_number=1, scene_setting="classroom"):
        """Generate a complete lesson using the LLM"""
        try:
            if grammar_points is None:
                grammar_points = []
            if vocabulary_focus is None:
                vocabulary_focus = []
                
            response = requests.post(
                f"{LLM_TEXT_ENDPOINT}/generate-lesson",
                json={
                    "topic": topic,
                    "grammar_points": grammar_points,
                    "vocabulary_focus": vocabulary_focus,
                    "lesson_number": lesson_number,
                    "scene_setting": scene_setting
                }
            )
            
            if response.status_code != 200:
                print(f"Lesson generation failed: {response.text}")
                return None
                
            result = response.json()
            
            # Check if we got a valid lesson structure
            if "lesson" in result:
                return result["lesson"]
            elif "metadata" in result and "dialogue_script" in result:
                return result
            elif "error" in result:
                print(f"Lesson generation error: {result['error']}")
                return None
            else:
                print("Unexpected response format from lesson generator")
                return None
        except Exception as e:
            print(f"Lesson generation failed: {str(e)}")
            return None