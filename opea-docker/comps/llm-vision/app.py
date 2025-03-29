from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Dict, Any, Union
import httpx
import os
import base64
from enum import Enumfrom pathlib import Path
import importlib.util
import io
from PIL import Image

# Force CPU mode for MangaOCR if needed
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"from pathlib import Path
import importlib.util
import io
from PIL import ImageMANGAOCR_MODELS_PATH = os.getenv("MANGAOCR_MODELS_PATH", "/app/mangaocr_models")

# Check if manga_ocr is installed
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Initialize MangaOCR if available
manga_ocr_available = is_package_installed("manga_ocr")
if manga_ocr_available:
    try:
        import manga_ocr
        print("MangaOCR module loaded successfully")
    except Exception as e:
        print(f"Error importing MangaOCR: {e}")
        manga_ocr_available = False
else:
    print("MangaOCR module not found")
# Force CPU mode for MangaOCR if needed
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Constants
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://ollama-server:11434")
VISION_MODEL_ID = os.getenv("VISION_MODEL_ID", "llava")
MANGAOCR_MODELS_PATH = os.getenv("MANGAOCR_MODELS_PATH", "/app/mangaocr_models")

# Check if manga_ocr is installed
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Initialize MangaOCR if available
manga_ocr_available = is_package_installed("manga_ocr")
if manga_ocr_available:
    try:
        import manga_ocr
        print("MangaOCR module loaded successfully")
    except Exception as e:
        print(f"Error importing MangaOCR: {e}")
        manga_ocr_available = False
else:
    print("MangaOCR module not found")

class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    USER = "user"
    ASSISTANT = "assistant"
# Initialize MangaOCR
_manga_ocr = None

def get_manga_ocr():
    global _manga_ocr
    if _manga_ocr is None and manga_ocr_available:
        try:
            print(f"Initializing MangaOCR with models path: {MANGAOCR_MODELS_PATH}")
            _manga_ocr = manga_ocr.MangaOcr()
            print("MangaOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing MangaOCR: {e}")
    return _manga_ocr

# Process image with MangaOCR
def process_image_with_ocr(image):
    ocr = get_manga_ocr()
    if ocr is None:
        return "OCR not available"

    try:
        # Convert to PIL Image if it's not already
        if not isinstance(image, Image.Image):
            image = Image.open(image)

        # Save to a temporary file (MangaOCR works better with files)
        temp_path = "/tmp/temp_image.png"
        image.save(temp_path)

        # Process with OCR
        text = ocr(temp_path)

        # Clean up
        if Path(temp_path).exists():
            Path(temp_path).unlink()

        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return "Error processing image"

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...), language: Optional[str] = Form("auto")):
    """Extract text from an image using MangaOCR.
    
    This endpoint is specifically designed for Japanese text in manga/comics.
    """
    if not manga_ocr_available:
        raise HTTPException(status_code=501, detail="MangaOCR is not available on this server")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Process with MangaOCR
        text = process_image_with_ocr(image)
        
        return OCRResponse(
            text=text,
            language="ja",  # MangaOCR is specifically for Japanese
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

class Content(BaseModel):
    type: str  # "text" or "image_url"
    text: Optional[str] = None
    image_url: Optional[dict] = None

class Message(BaseModel):
    role: Role
    content: List[Content]

class VisionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class VisionResponse(BaseModel):
    model: str
    content: str
    done: bool

class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None

# Initialize FastAPI app
app = FastAPI()

# Initialize MangaOCR
_manga_ocr = None

def get_manga_ocr():
    global _manga_ocr
    if _manga_ocr is None and manga_ocr_available:
        try:
            print(f"Initializing MangaOCR with models path: {MANGAOCR_MODELS_PATH}")
            _manga_ocr = manga_ocr.MangaOcr()
            print("MangaOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing MangaOCR: {e}")
    return _manga_ocr

# Process image with MangaOCR
def process_image_with_ocr(image):
    ocr = get_manga_ocr()
    if ocr is None:
        return "OCR not available"

    try:
        # Convert to PIL Image if it's not already
        if not isinstance(image, Image.Image):
            image = Image.open(image)

        # Save to a temporary file (MangaOCR works better with files)
        temp_path = "/tmp/temp_image.png"
        image.save(temp_path)

        # Process with OCR
        text = ocr(temp_path)

        # Clean up
        if Path(temp_path).exists():
            Path(temp_path).unlink()

        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return "Error processing image"

@app.post("/v1/vision")
async def vision_completion(request: VisionRequest):
    try:
        # Format messages for Ollama
        ollama_messages = []
        
        for msg in request.messages:
            content_list = []
            for content in msg.content:
                if content.type == "text":
                    content_list.append({"type": "text", "text": content.text})
                elif content.type == "image_url":
                    content_list.append({"type": "image", "image": content.image_url})
            
            ollama_messages.append({"role": msg.role, "content": content_list})

        # Prepare the request for Ollama
        ollama_request = {
            "model": request.model or VISION_MODEL_ID,
            "messages": ollama_messages,
            "stream": False,
            "temperature": request.temperature
        }

        # Make request to Ollama
        async with httpx.AsyncClient() as client:
            # First, ensure the model is pulled
            try:
                await client.post(
                    f"{LLM_ENDPOINT}/api/pull",
                    json={"name": request.model or VISION_MODEL_ID},
                    timeout=30.0
                )
            except Exception as e:
                print(f"Warning: Model pull failed: {e}")

            # Make the generation request
            response = await client.post(
                f"{LLM_ENDPOINT}/api/chat",  # Using chat API for vision models
                json=ollama_request,
                timeout=60.0  # Increased timeout for generation
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error from LLM service: {response.text}"
                )

            result = response.json()

            # Handle different response formats
            content = ""
            if "response" in result:  # Ollama generate API
                content = result["response"]
            elif "message" in result:  # Ollama chat API
                content = result["message"]["content"]

            return VisionResponse(
                model=request.model or VISION_MODEL_ID,
                content=content,
                done=True
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

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
            "status": "healthy", 
            "ollama_status": f"error: {str(e)}",
            "manga_ocr_status": "unknown"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9100)