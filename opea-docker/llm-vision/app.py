from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import httpx
import os
import base64
from enum import Enum
from pathlib import Path
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

# Configuration
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://llm:11434")
VISION_MODEL_ID = os.environ.get("VISION_MODEL_ID", "llava-hf/llava-1.5-7b-hf")
MODEL_CACHE_DIR = os.environ.get("TRANSFORMERS_CACHE", "/app/data/llava_models")

# Initialize FastAPI app
app = FastAPI()

# Global variables
_llava_processor = None
_llava_model = None

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

def get_llava_model():
    global _llava_processor, _llava_model
    if _llava_processor is None or _llava_model is None:
        try:
            _llava_processor = AutoProcessor.from_pretrained(
                VISION_MODEL_ID,
                cache_dir=MODEL_CACHE_DIR
            )
            _llava_model = AutoModelForCausalLM.from_pretrained(
                VISION_MODEL_ID,
                cache_dir=MODEL_CACHE_DIR,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        except Exception as e:
            print(f"Warning: LLaVA model initialization failed: {e}")
    return _llava_processor, _llava_model

@app.post("/vision")
async def process_vision(request: VisionRequest):
    try:
        processor, model = get_llava_model()
        if processor is None or model is None:
            raise HTTPException(status_code=500, detail="LLaVA model not initialized")

        # Decode base64 image
        image_data = base64.b64decode(request.image.split(",")[1])
        
        # Process image and text
        inputs = processor(
            text=request.prompt,
            images=image_data,
            return_tensors="pt"
        ).to(model.device)

        # Generate response
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True
        )
        
        # Decode response
        response_text = processor.decode(outputs[0], skip_special_tokens=True)
        
        return VisionResponse(
            model=VISION_MODEL_ID,
            content=response_text,
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
            
        # Check LLaVA status
        processor, model = get_llava_model()
        llava_status = "initialized" if processor is not None and model is not None else "not initialized"
            
        return {
            "status": "healthy", 
            "ollama_status": ollama_status, 
            "model": VISION_MODEL_ID,
            "llava_status": llava_status
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "llava_status": "unknown"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VISION_SERVICE_PORT", 9101))
    uvicorn.run(app, host="0.0.0.0", port=port)