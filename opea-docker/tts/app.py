from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import base64
import tempfile
from contextlib import asynccontextmanager
import torch
import logging
import traceback
from TTS.api import TTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TTS_DATA_PATH = os.getenv("TTS_DATA_PATH", "/app/data/tts_data")
VOICES_PATH = os.path.join(TTS_DATA_PATH, "voices")
MALE_VOICE_PATH = os.path.join(VOICES_PATH, "male_voice.wav")
FEMALE_VOICE_PATH = os.path.join(VOICES_PATH, "female_voice.wav")

os.makedirs(TTS_DATA_PATH, exist_ok=True)
logger.info(f"TTS data path: {TTS_DATA_PATH}")
logger.info(f"Directory contents: {os.listdir(TTS_DATA_PATH)}")

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None  # 'male' or 'female' or path to speaker wav
    language: Optional[str] = "en"
    speed: Optional[float] = 1.0

class TTSResponse(BaseModel):
    audio: str  # base64 encoded audio
    format: str = "wav"

_tts_model = None

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        try:
            logger.info("Loading Coqui XTTS v2 model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            logger.info(f"Coqui XTTS v2 model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load Coqui XTTS v2: {e}")
            if device == "cuda":
                logger.info("Attempting to fall back to CPU...")
                device = "cpu"
                try:
                    _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
                    logger.info("Coqui XTTS v2 model loaded successfully on CPU")
                except Exception as e:
                    logger.error(f"Failed to load Coqui XTTS v2 on CPU: {e}")
                    raise e
    return _tts_model

def resolve_voice_path(voice_id: Optional[str]) -> Optional[str]:
    if not voice_id:
        return None
    if voice_id.lower() == "male":
        return MALE_VOICE_PATH if os.path.exists(MALE_VOICE_PATH) else None
    if voice_id.lower() == "female":
        return FEMALE_VOICE_PATH if os.path.exists(FEMALE_VOICE_PATH) else None
    # If a path is provided, check if it exists
    if os.path.exists(voice_id):
        return voice_id
    logger.warning(f"Voice reference file not found: {voice_id}")
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up TTS service...")
    try:
        get_tts_model()
        logger.info("TTS model initialized during startup")
    except Exception as e:
        logger.error(f"Failed to initialize TTS model during startup: {e}")
    yield
    logger.info("Shutting down TTS service...")

app = FastAPI(lifespan=lifespan)

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        tts = get_tts_model()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_filename = temp_file.name

        speaker_wav = resolve_voice_path(request.voice_id)
        logger.info(f"Using speaker_wav: {speaker_wav}")

        # Synthesize speech
        tts.tts_to_file(
            text=request.text,
            speaker_wav=speaker_wav,
            language=request.language,
            file_path=temp_filename
        )

        with open(temp_filename, "rb") as audio_file:
            audio_data = audio_file.read()
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        os.unlink(temp_filename)
        return TTSResponse(audio=audio_base64, format="wav")
    except Exception as e:
        logger.error(f"Error in text_to_speech: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/health")
async def health_check():
    model_files = os.listdir(TTS_DATA_PATH) if os.path.exists(TTS_DATA_PATH) else []
    return {
        "status": "healthy",
        "model_files": model_files,
        "tts_home": os.environ.get("TTS_HOME", "not set"),
        "directory_exists": os.path.exists(TTS_DATA_PATH),
        "directory_permissions": oct(os.stat(TTS_DATA_PATH).st_mode)[-3:] if os.path.exists(TTS_DATA_PATH) else "N/A"
    }

@app.get("/voices")
async def list_voices():
    voices = []
    if os.path.exists(VOICES_PATH):
        voices = [f for f in os.listdir(VOICES_PATH) if f.endswith('.wav')]
    return {"voices": voices}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TTS_SERVICE_PORT", 9200))
    uvicorn.run(app, host="0.0.0.0", port=port)