from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import base64
import tempfile
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts, XttsAudioConfig, XttsArgs
from contextlib import asynccontextmanager
import torch
import logging
import torch.serialization
from TTS.config.shared_configs import BaseDatasetConfig
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add XttsConfig, XttsAudioConfig to safe globals for PyTorch 2.6+
torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

TTS_DATA_PATH = os.getenv("TTS_DATA_PATH", "/app/data/tts_data")
XTTS_CONFIG_PATH = os.path.join(TTS_DATA_PATH, "config.json")
XTTS_CHECKPOINT_DIR = TTS_DATA_PATH

os.makedirs(TTS_DATA_PATH, exist_ok=True)
logger.info(f"TTS data path: {TTS_DATA_PATH}")
logger.info(f"Directory contents: {os.listdir(TTS_DATA_PATH)}")

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None  # path to speaker wav
    language: Optional[str] = "en"
    speed: Optional[float] = 1.0

class TTSResponse(BaseModel):
    audio: str  # base64 encoded audio
    format: str = "wav"

_xtts_model = None

def get_xtts_model():
    global _xtts_model
    if _xtts_model is None:
        try:
            logger.info("Loading XTTS v2 model...")
            config = XttsConfig()
            config.load_json(XTTS_CONFIG_PATH)
            model = Xtts.init_from_config(config)
            model.load_checkpoint(config, checkpoint_dir=XTTS_CHECKPOINT_DIR, eval=True)
            
            # Check if CUDA is available and use it if possible
            if torch.cuda.is_available():
                logger.info("Using CUDA for TTS model")
                model.cuda()
            else:
                logger.info("CUDA not available, using CPU for TTS model")
                model.cpu()
                
            _xtts_model = (model, config)
            logger.info("XTTS v2 model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load XTTS v2: {e}\n{traceback.format_exc()}")
            raise
    return _xtts_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up TTS service...")
    try:
        get_xtts_model()
        logger.info("TTS model initialized during startup")
    except Exception as e:
        logger.error(f"Failed to initialize TTS model during startup: {e}")
    yield
    # Shutdown
    logger.info("Shutting down TTS service...")

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        (model, config) = get_xtts_model()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_filename = temp_file.name

        # XTTS requires a speaker wav for voice cloning; if not provided, use a default or skip
        speaker_wav = request.voice if request.voice else None

        outputs = model.synthesize(
            request.text,
            config,
            speaker_wav=speaker_wav,
            gpt_cond_len=3,
            language=request.language,
        )
        # Save the output waveform to file
        model.save_wav(outputs["wav"], temp_filename, sample_rate=outputs["sample_rate"])

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
    # This would list available voices in a real implementation
    return {"voices": ["default", "male1", "female1", "child1"]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TTS_SERVICE_PORT", 9200))
    uvicorn.run(app, host="0.0.0.0", port=port)