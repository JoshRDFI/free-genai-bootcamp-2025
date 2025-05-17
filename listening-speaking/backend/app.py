# backend/app.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import uvicorn
import logging
from datetime import datetime
import os

from backend.youtube.get_transcript import YouTubeTranscriptDownloader
from backend.llm.question_generator import QuestionGenerator
from backend.database.knowledge_base import KnowledgeBase
from backend.tts.tts_engine import TTSEngine
from backend.asr.asr_engine import ASREngine
from backend.image.image_generator import ImageGenerator
from backend.utils.helper import ensure_directories_exist
from backend.config import ServiceConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Debug log environment variables
logger.info("Environment variables:")
for var in ["BACKEND_PORT", "LLM_TEXT_PORT", "TTS_SERVICE_PORT", "ASR_SERVICE_PORT", 
            "LLM_VISION_PORT", "EMBEDDING_SERVICE_PORT", "TTS_DATA_PATH"]:
    logger.info(f"{var}: {os.getenv(var)}")

logger.info("Starting FastAPI application...")
try:
    app = FastAPI(
        title="JLPT Listening Practice API",
        description="API for Japanese listening comprehension practice",
        version="1.0.0"
    )
    logger.info("FastAPI application created successfully")

    # Add CORS middleware
    logger.info("Adding CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added successfully")

    # Initialize components
    try:
        logger.info("Starting component initialization...")
        
        logger.info("Initializing transcript downloader...")
        transcript_downloader = YouTubeTranscriptDownloader()
        logger.info("Transcript downloader initialized successfully")
        
        logger.info("Initializing question generator...")
        question_generator = QuestionGenerator()
        logger.info("Question generator initialized successfully")
        
        logger.info("Initializing knowledge base...")
        knowledge_base = KnowledgeBase()
        logger.info("Knowledge base initialized successfully")
        
        logger.info("Initializing TTS engine...")
        tts_engine = TTSEngine()
        logger.info("TTS engine initialized successfully")
        
        logger.info("Initializing ASR engine...")
        asr_engine = ASREngine()
        logger.info("ASR engine initialized successfully")
        
        logger.info("Initializing image generator...")
        image_generator = ImageGenerator()
        logger.info("Image generator initialized successfully")
        
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}", exc_info=True)
        raise

    # Ensure required directories exist
    logger.info("Ensuring required directories exist...")
    ensure_directories_exist()
    logger.info("Directory check completed")

except Exception as e:
    logger.error(f"Failed to initialize FastAPI application: {str(e)}", exc_info=True)
    raise

# Request/Response Models
class VideoURL(BaseModel):
    url: HttpUrl

class Question(BaseModel):
    video_id: str
    section_num: int
    question_text: str

class AudioRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "default"
    language: Optional[str] = "ja"

class TranscriptionRequest(BaseModel):
    audio_data: bytes
    language: Optional[str] = "ja"

class ImageRequest(BaseModel):
    prompt: str
    style: Optional[str] = "anime"

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/services")
async def service_health_check():
    """Check health of all dependent services"""
    services = {
        "llm": ServiceConfig.get_endpoint("llm", "generate"),
        "tts": ServiceConfig.get_endpoint("tts", "synthesize"),
        "asr": ServiceConfig.get_endpoint("asr", "transcribe"),
        "vision": ServiceConfig.get_endpoint("vision", "analyze")
    }
    
    health_status = {}
    for service, endpoint in services.items():
        try:
            response = requests.get(endpoint.replace("/generate", "/health"))
            health_status[service] = response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {service}: {str(e)}")
            health_status[service] = False
    
    return {
        "status": "healthy" if all(health_status.values()) else "degraded",
        "services": health_status,
        "timestamp": datetime.now().isoformat()
    }

# Video processing endpoints
@app.post("/process-video")
async def process_video(video_data: VideoURL, background_tasks: BackgroundTasks):
    """Process a YouTube video URL"""
    try:
        # Get transcript
        result = transcript_downloader.process_video(str(video_data.url))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to process video")

        # Save to database
        video_id = result["video_id"]
        transcript_text = "\n".join(item["text"] for item in result["transcript"])
        knowledge_base.save_transcript(video_id, transcript_text)

        # Generate questions in background
        background_tasks.add_task(
            process_questions,
            result["transcript"],
            video_id
        )

        return {
            "status": "processing",
            "video_id": video_id,
            "message": "Video processing started"
        }

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_questions(transcript: List[Dict], video_id: str):
    """Background task to process questions"""
    try:
        questions = question_generator.generate_questions(transcript, video_id)
        for question in questions:
            knowledge_base.save_question(question)
        logger.info(f"Generated {len(questions)} questions for video {video_id}")
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")

@app.get("/questions/{video_id}")
async def get_questions(video_id: str):
    """Get questions for a video"""
    try:
        questions = knowledge_base.get_questions(video_id)
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found")
        return questions
    except Exception as e:
        logger.error(f"Error retrieving questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# TTS endpoints
@app.post("/tts/synthesize")
async def synthesize_speech(request: AudioRequest):
    """Synthesize speech from text"""
    try:
        audio_data = tts_engine.synthesize_speech(
            request.text,
            request.voice_id,
            request.language
        )
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        return {"audio_data": audio_data}
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tts/voices")
async def get_voices():
    """Get available voices"""
    try:
        voices = tts_engine.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ASR endpoints
@app.post("/asr/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio data"""
    try:
        result = asr_engine.transcribe_audio(
            request.audio_data,
            request.language
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
        return result
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/asr/languages")
async def get_supported_languages():
    """Get supported languages"""
    try:
        languages = asr_engine.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Vision endpoints
@app.post("/vision/generate")
async def generate_image(request: ImageRequest):
    """Generate image from prompt"""
    try:
        image_data = image_generator.generate_image(
            request.prompt,
            request.style
        )
        if not image_data:
            raise HTTPException(status_code=500, detail="Failed to generate image")
        return {"image_data": image_data}
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8180)  # Changed port to avoid conflicts with other services