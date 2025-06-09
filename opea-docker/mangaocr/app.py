from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import httpx
import os
import base64
from enum import Enum
from pathlib import Path

# Configuration
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://llm:11434")
VISION_MODEL_ID = os.environ.get("VISION_MODEL_ID", "llava:13b")

# Initialize FastAPI app
app = FastAPI()

# Global variables
_manga_ocr = None
manga_ocr_available = False

# Try to import MangaOCR
print("Initializing MangaOCR module")
try:
    from manga_ocr import MangaOcr
    manga_ocr_available = True
except ImportError:
    print("MangaOCR not available")
    manga_ocr_available = False

# Models
class VisionRequest(BaseModel):
    model: Optional[str] = None
    prompt: str
    image: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class VisionResponse(BaseModel):
    model: str
    content: str
    done: bool

# Helper functions
def get_manga_ocr():
    global _manga_ocr
    if _manga_ocr is None:
        try:
            # Try to use GPU first, fall back to CPU if not available or compatible
            import torch
            if torch.cuda.is_available():
                try:
                    _manga_ocr = MangaOcr()
                except RuntimeError as e:
                    if "CUDA" in str(e):
                        print(f"GPU not compatible, falling back to CPU: {e}")
                        _manga_ocr = MangaOcr(force_cpu=True)
                    else:
                        raise
            else:
                print("CUDA not available, using CPU")
                _manga_ocr = MangaOcr(force_cpu=True)
        except Exception as e:
            print(f"Warning: Model initialization failed: {e}")
    return _manga_ocr

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...), language: Optional[str] = Form("ja")):
    try:
        if not manga_ocr_available:
            raise HTTPException(status_code=500, detail="MangaOCR not available")
            
        ocr = get_manga_ocr()
        if ocr is None:
            raise HTTPException(status_code=500, detail="MangaOCR failed to initialize")
            
        # Read the uploaded file
        contents = await file.read()
        
        # Process with MangaOCR
        text = ocr(contents)
        
        return {"text": text, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/vision")
async def process_vision(request: VisionRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_ENDPOINT}/api/chat",  # Using chat API for vision models
                json={
                    "model": request.model or VISION_MODEL_ID,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": request.prompt},
                                {"type": "image_url", "image_url": {"url": request.image}}
                            ]
                        }
                    ],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM service error: {response.text}"
                )
                
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            return VisionResponse(
                model=request.model or VISION_MODEL_ID,
                content=content,
                done=True
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode("utf-8")
        return {"image_url": {"url": f"data:image/{file.content_type.split('/')[-1]};base64,{encoded}"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        # Check if Ollama server is responsive
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_ENDPOINT}/api/version")
            ollama_status = "connected" if response.status_code == 200 else "disconnected"
            
        # Check MangaOCR status
        manga_ocr_status = "available" if manga_ocr_available else "not available"
        if manga_ocr_available:
            ocr = get_manga_ocr()
            manga_ocr_status = "initialized" if ocr is not None else "not initialized"
            
        return {
            "status": "healthy", 
            "ollama_status": ollama_status, 
            "model": VISION_MODEL_ID,
            "manga_ocr_status": manga_ocr_status
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "manga_ocr_status": "unknown"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VISION_SERVICE_PORT", 9100))
    uvicorn.run(app, host="0.0.0.0", port=port)