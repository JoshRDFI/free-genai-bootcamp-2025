from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import base64
import tempfile
import whisper

# Constants
ASR_MODEL = os.getenv("ASR_MODEL", "large-v3")

class ASRResponse(BaseModel):
    text: str
    confidence: float
    language: str

# Initialize FastAPI app
app = FastAPI()

# Initialize Whisper model
_asr_model = None

def get_asr_model():
    global _asr_model
    if _asr_model is None:
        try:
            print(f"Initializing Whisper model: {ASR_MODEL}")
            _asr_model = whisper.load_model(ASR_MODEL)
            print("Whisper model initialized successfully")
        except Exception as e:
            print(f"Error initializing Whisper model: {e}")
    return _asr_model

def speech_to_text(audio_file_path):
    try:
        model = get_asr_model()
        if model is None:
            raise Exception("ASR model failed to initialize")
            
        # Process with Whisper
        result = model.transcribe(audio_file_path)
        
        # Extract results
        text = result["text"]
        language = result.get("language", "unknown")
        confidence = result.get("confidence", 0.95)  # Whisper doesn't provide confidence, using default
        
        return text, confidence, language
    except Exception as e:
        raise Exception(f"ASR processing failed: {str(e)}")

@app.post("/asr")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        # Process the audio file
        text, confidence, language = speech_to_text(temp_filename)
        
        # Clean up
        os.unlink(temp_filename)
        
        return ASRResponse(text=text, confidence=confidence, language=language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@app.post("/asr-base64")
async def transcribe_audio_base64(audio_base64: str):
    try:
        # Decode the base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        # Process the audio file
        text, confidence, language = speech_to_text(temp_filename)
        
        # Clean up
        os.unlink(temp_filename)
        
        return ASRResponse(text=text, confidence=confidence, language=language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": ASR_MODEL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9300)