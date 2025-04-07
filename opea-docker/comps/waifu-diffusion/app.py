from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline
import torch
import os
import io
from typing import Optional
import base64
from PIL import Image

# Initialize FastAPI app
app = FastAPI()

# Environment variables
MODEL_ID = os.getenv("MODEL_ID", "waifu-diffusion/wd-1-5-beta2")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/data/waifu")
USE_LOCAL = os.getenv("USE_LOCAL", "True").lower() in ("true", "1", "t")

# Check if CUDA is available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the Waifu Diffusion model
def load_model():
    try:
        if USE_LOCAL and os.path.exists(MODEL_PATH):
            print(f"Loading model from local path: {MODEL_PATH}")
            pipe = StableDiffusionPipeline.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)
        else:
            print(f"Downloading model from Hugging Face: {MODEL_ID}")
            pipe = StableDiffusionPipeline.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)
            
            # Save the model locally if USE_LOCAL is True
            if USE_LOCAL:
                print(f"Saving model to: {MODEL_PATH}")
                os.makedirs(MODEL_PATH, exist_ok=True)
                pipe.save_pretrained(MODEL_PATH)
                
        return pipe
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e

# Request model
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    num_inference_steps: Optional[int] = 50
    guidance_scale: Optional[float] = 7.5
    width: Optional[int] = 512
    height: Optional[int] = 512
    return_format: Optional[str] = "base64"  # 'base64' or 'binary'

# Initialize the model
pipe = None

@app.on_event("startup")
async def startup_event():
    global pipe
    pipe = load_model()

@app.post("/generate")
async def generate_image(request: ImageRequest):
    global pipe
    
    if pipe is None:
        pipe = load_model()
    
    try:
        # Generate the image
        image = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            width=request.width,
            height=request.height
        ).images[0]
        
        # Prepare the response
        if request.return_format == "binary":
            # Return the image as binary data
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            return Response(content=img_byte_arr.getvalue(), media_type="image/png")
        else:
            # Return the image as base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"status": "success", "image": img_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    global pipe
    
    try:
        # Check if model is loaded
        model_status = "loaded" if pipe is not None else "not_loaded"
        
        # Check if CUDA is available
        cuda_status = "available" if torch.cuda.is_available() else "not_available"
        
        return {
            "status": "healthy",
            "model": MODEL_ID,
            "model_status": model_status,
            "device": device,
            "cuda_status": cuda_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9500)