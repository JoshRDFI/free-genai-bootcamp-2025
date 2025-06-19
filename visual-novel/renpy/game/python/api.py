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
OLLAMA_SERVER_URL = os.environ.get('OLLAMA_SERVER_URL', 'http://localhost:11434')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')
LLM_TEXT_ENDPOINT = os.environ.get('LLM_TEXT_URL', 'http://localhost:11434')
GUARDRAILS_URL = os.environ.get('GUARDRAILS_URL', 'http://localhost:9400/v1/guardrails')
CHROMADB_URL = os.environ.get('CHROMADB_URL', 'http://localhost:8000')
TTS_ENDPOINT = os.environ.get('TTS_URL', 'http://localhost:9200')
ASR_ENDPOINT = os.environ.get('ASR_URL', 'http://localhost:9300')
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
                f"{LLM_TEXT_ENDPOINT}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Provide only the translation, no explanations."
                        },
                        {
                            "role": "user", 
                            "content": text
                        }
                    ],
                    "stream": False
                }
            )
            result = response.json()
            return result.get("message", {}).get("content", "Translation failed")
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return "Translation failed"
    
    @staticmethod
    def get_audio(text, voice="ja-JP"):
        """Get audio for text using TTS service"""
        try:
            response = requests.post(
                f"{TTS_ENDPOINT}/generate",
                json={
                    "text": text,
                    "voice": voice,
                    "language": "ja"
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
                
            # Create a prompt for conversation generation
            prompt = f"""
            Generate a natural Japanese conversation with the following context:
            Context: {context}
            Characters: {', '.join(characters)}
            Grammar points to include: {', '.join(grammar_points)}
            Vocabulary to include: {', '.join(vocabulary)}
            Number of exchanges: {num_exchanges}
            
            Please provide the conversation in JSON format with the following structure:
            {{
                "conversation": [
                    {{"speaker": "Character1", "japanese": "こんにちは", "english": "Hello"}},
                    {{"speaker": "Character2", "japanese": "こんにちは", "english": "Hello"}}
                ]
            }}
            """
                
            response = requests.post(
                f"{LLM_TEXT_ENDPOINT}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a Japanese language teacher. Generate natural conversations that help students learn Japanese."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                print(f"Conversation generation failed: {response.text}")
                return None
                
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # Try to parse the JSON response
            try:
                import json
                conversation_data = json.loads(content)
                if "conversation" in conversation_data:
                    return conversation_data["conversation"]
                else:
                    print("Unexpected response format from conversation generator")
                    return None
            except json.JSONDecodeError:
                print("Failed to parse conversation response as JSON")
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
                
            # Create a prompt for lesson generation
            prompt = f"""
            Generate a complete Japanese lesson with the following details:
            Topic: {topic}
            Lesson Number: {lesson_number}
            Scene Setting: {scene_setting}
            Grammar points to cover: {', '.join(grammar_points)}
            Vocabulary focus: {', '.join(vocabulary_focus)}
            
            Please provide the lesson in JSON format with the following structure:
            {{
                "lesson": {{
                    "title": "Lesson Title",
                    "topic": "{topic}",
                    "grammar_points": ["grammar1", "grammar2"],
                    "vocabulary": [
                        {{"japanese": "こんにちは", "reading": "konnichiwa", "english": "hello"}}
                    ],
                    "dialogue": [
                        {{"speaker": "Teacher", "japanese": "こんにちは", "english": "Hello"}},
                        {{"speaker": "Student", "japanese": "こんにちは", "english": "Hello"}}
                    ]
                }}
            }}
            """
                
            response = requests.post(
                f"{LLM_TEXT_ENDPOINT}/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a Japanese language teacher. Generate comprehensive lessons that help students learn Japanese effectively."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                print(f"Lesson generation failed: {response.text}")
                return None
                
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # Try to parse the JSON response
            try:
                import json
                lesson_data = json.loads(content)
                if "lesson" in lesson_data:
                    return lesson_data["lesson"]
                else:
                    print("Unexpected response format from lesson generator")
                    return None
            except json.JSONDecodeError:
                print("Failed to parse lesson response as JSON")
                return None
        except Exception as e:
            print(f"Lesson generation failed: {str(e)}")
            return None