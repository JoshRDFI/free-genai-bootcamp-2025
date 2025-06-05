from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import httpx
import os
import base64
from enum import Enum
from pathlib import Path
import torch
from transformers import LlavaForConditionalGeneration, LlavaProcessor
from PIL import Image
import io

# Configuration
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://ollama-server:11434")
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
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Using device: {device}")
            
            _llava_processor = LlavaProcessor.from_pretrained(
                VISION_MODEL_ID,
                cache_dir=MODEL_CACHE_DIR
            )
            _llava_model = LlavaForConditionalGeneration.from_pretrained(
                VISION_MODEL_ID,
                cache_dir=MODEL_CACHE_DIR,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            ).to(device)
            
            print(f"LLaVA model loaded successfully on {device}")
        except Exception as e:
            print(f"Warning: LLaVA model initialization failed: {e}")
            if device == "cuda":
                print("Attempting to fall back to CPU...")
                device = "cpu"
                try:
                    _llava_processor = LlavaProcessor.from_pretrained(
                        VISION_MODEL_ID,
                        cache_dir=MODEL_CACHE_DIR
                    )
                    _llava_model = LlavaForConditionalGeneration.from_pretrained(
                        VISION_MODEL_ID,
                        cache_dir=MODEL_CACHE_DIR,
                        torch_dtype=torch.float32,
                        device_map=None
                    ).to(device)
                    print("LLaVA model loaded successfully on CPU")
                except Exception as e:
                    print(f"Failed to load LLaVA model on CPU: {e}")
                    raise e
    return _llava_processor, _llava_model

@app.post("/vision")
async def process_vision(request: VisionRequest):
    try:
        processor, model = get_llava_model()
        if processor is None or model is None:
            raise HTTPException(status_code=500, detail="LLaVA model not initialized")

        # Decode base64 image and convert to PIL Image
        image_data = base64.b64decode(request.image.split(",")[1])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        # Format the prompt properly for LLaVA
        prompt = f"USER: <image>\n{request.prompt}\nASSISTANT:"

        # Process image and text
        inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(model.device)

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True,
                pad_token_id=processor.tokenizer.eos_token_id
            )

        # Decode response and extract only the assistant's response
        full_response = processor.decode(outputs[0], skip_special_tokens=True)
        # Extract only the assistant's response (after "ASSISTANT:")
        response_text = full_response.split("ASSISTANT:")[-1].strip()

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