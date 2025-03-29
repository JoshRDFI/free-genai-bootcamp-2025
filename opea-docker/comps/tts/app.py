from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import base64
import tempfile
from TTS.api import TTS

# Constants
TTS_MODEL = os.getenv("TTS_MODEL", "xtts-v2")
TTS_DATA_PATH = os.getenv("TTS_DATA_PATH", "/home/tts/.xtts_data")

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"
    language: Optional[str] = "en"
    speed: Optional[float] = 1.0

class TTSResponse(BaseModel):
    audio: str  # base64 encoded audio
    format: str = "wav"

# Initialize FastAPI app
app = FastAPI()

# Initialize TTS model
_tts_model = None

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        try:
            print(f"Initializing TTS model: {TTS_MODEL}")
            _tts_model = TTS(model_name=TTS_MODEL)
            print("TTS model initialized successfully")
        except Exception as e:
            print(f"Error initializing TTS model: {e}")
    return _tts_model

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        # Get the TTS model
        tts = get_tts_model()
        if tts is None:
            raise Exception("TTS model failed to initialize")
            
        # Create a temporary file for the audio output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_filename = temp_file.name
        
        # Generate speech with XTTS
        tts.tts_to_file(
            text=request.text,
            file_path=temp_filename,
            speaker=request.voice,
            language=request.language,
            speed=request.speed
        )
        
        # Read the generated audio file
        with open(temp_filename, "rb") as audio_file:
            audio_data = audio_file.read()
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        # Clean up
        os.unlink(temp_filename)
        
        return TTSResponse(audio=audio_base64, format="wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": TTS_MODEL}

@app.get("/voices")
async def list_voices():
    # This would list available voices in a real implementation
    return {"voices": ["default", "male1", "female1", "child1"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9200)