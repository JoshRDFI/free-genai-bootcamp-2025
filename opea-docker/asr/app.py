from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import base64
import tempfile
import whisper
import logging
import librosa
import soundfile as sf
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ASR_MODEL = os.getenv("ASR_MODEL", "base")  # Changed from large-v3 to base for faster processing

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
            logger.info(f"Initializing Whisper model: {ASR_MODEL}")
            _asr_model = whisper.load_model(ASR_MODEL)
            logger.info("Whisper model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Whisper model: {e}")
    return _asr_model

def preprocess_audio(audio_file_path: str) -> str:
    """
    Preprocess audio to reduce file size and improve processing speed.
    - Resample to 16kHz (Whisper's preferred sample rate)
    - Convert to mono if stereo
    - Normalize audio levels
    - For very large files, chunk them into smaller segments
    """
    try:
        logger.info(f"Preprocessing audio file: {audio_file_path}")
        
        # Load audio with librosa
        audio, sr = librosa.load(audio_file_path, sr=None, mono=False)
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=0)
            logger.info("Converted stereo to mono")
        
        # Resample to 16kHz if needed
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            logger.info(f"Resampled from {sr}Hz to 16000Hz")
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        # Check if file is very large (> 10MB) and chunk if necessary
        duration = len(audio) / 16000  # Duration in seconds
        if duration > 300:  # If longer than 5 minutes, chunk it
            logger.info(f"Audio is {duration:.1f} seconds long, chunking into segments")
            chunk_duration = 300  # 5 minutes per chunk
            chunk_samples = int(chunk_duration * 16000)
            
            # Create chunks directory
            chunks_dir = os.path.join(os.path.dirname(audio_file_path), "chunks")
            os.makedirs(chunks_dir, exist_ok=True)
            
            # Split audio into chunks
            chunks = []
            for i in range(0, len(audio), chunk_samples):
                chunk = audio[i:i + chunk_samples]
                chunk_path = os.path.join(chunks_dir, f"chunk_{i//chunk_samples}.wav")
                sf.write(chunk_path, chunk, 16000)
                chunks.append(chunk_path)
                logger.info(f"Created chunk {i//chunk_samples}: {len(chunk)/16000:.1f}s")
            
            # Return the first chunk for now (we'll handle multiple chunks in speech_to_text)
            return chunks[0] if chunks else audio_file_path
        
        # Save preprocessed audio
        preprocessed_path = audio_file_path.replace('.wav', '_preprocessed.wav')
        sf.write(preprocessed_path, audio, 16000)
        
        logger.info(f"Audio preprocessing completed. Original size: {os.path.getsize(audio_file_path)}, Preprocessed size: {os.path.getsize(preprocessed_path)}")
        return preprocessed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing audio: {e}")
        return audio_file_path  # Return original file if preprocessing fails

def speech_to_text(audio_file_path):
    try:
        model = get_asr_model()
        if model is None:
            raise Exception("ASR model failed to initialize")
        
        # Check if this is a chunked file
        chunks_dir = os.path.join(os.path.dirname(audio_file_path), "chunks")
        if os.path.exists(chunks_dir):
            logger.info("Processing chunked audio file")
            chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.wav')])
            
            all_text = []
            for i, chunk_file in enumerate(chunk_files):
                chunk_path = os.path.join(chunks_dir, chunk_file)
                logger.info(f"Processing chunk {i+1}/{len(chunk_files)}: {chunk_file}")
                
                # Process each chunk
                result = model.transcribe(
                    chunk_path,
                    language="ja",
                    task="transcribe"
                )
                
                all_text.append(result["text"].strip())
                
                # Clean up chunk file
                os.unlink(chunk_path)
            
            # Clean up chunks directory
            os.rmdir(chunks_dir)
            
            # Combine all text
            full_text = " ".join(all_text)
            logger.info(f"Combined transcription from {len(chunk_files)} chunks. Total text length: {len(full_text)}")
            
            return full_text, 0.95, "ja"
        
        # Preprocess the audio (for non-chunked files)
        preprocessed_path = preprocess_audio(audio_file_path)
        
        logger.info(f"Starting transcription with model: {ASR_MODEL}")
        
        # Process with Whisper
        result = model.transcribe(
            preprocessed_path,
            language="ja",  # Specify Japanese for better accuracy
            task="transcribe"
        )
        
        # Extract results
        text = result["text"]
        language = result.get("language", "ja")
        confidence = result.get("confidence", 0.95)
        
        logger.info(f"Transcription completed. Text length: {len(text)}")
        
        # Clean up preprocessed file if it was created
        if preprocessed_path != audio_file_path and os.path.exists(preprocessed_path):
            os.unlink(preprocessed_path)
        
        return text, confidence, language
    except Exception as e:
        logger.error(f"ASR processing failed: {str(e)}")
        raise Exception(f"ASR processing failed: {str(e)}")

@app.post("/asr")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        logger.info(f"Received audio file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        logger.info(f"Saved temporary file: {temp_filename}")
        
        # Process the audio file
        text, confidence, language = speech_to_text(temp_filename)
        
        # Clean up
        os.unlink(temp_filename)
        
        logger.info("Transcription request completed successfully")
        return ASRResponse(text=text, confidence=confidence, language=language)
    except Exception as e:
        logger.error(f"Error in transcribe_audio endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@app.post("/asr-base64")
async def transcribe_audio_base64(audio_base64: str):
    try:
        logger.info("Received base64 audio data")
        
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
        logger.error(f"Error in transcribe_audio_base64 endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": ASR_MODEL}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ASR_SERVICE_PORT", 9300))
    uvicorn.run(app, host="0.0.0.0", port=port)