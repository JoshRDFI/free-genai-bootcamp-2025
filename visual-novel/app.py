from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline
import torch
import os
import base64
from io import BytesIO
from PIL import Image

# Initialize FastAPI app
app = FastAPI(title="Waifu Diffusion API", description="API for generating anime-style images")

# Load the Stable Diffusion model
model_path = os.environ.get("WAIFU_DIFFUSION_MODEL", "hakurei/waifu-diffusion")
cache_dir = os.environ.get("TRANSFORMERS_CACHE", "/app/model_cache")
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model {model_path} from cache directory {cache_dir} on device {device}")

# Check if model is already downloaded
if os.path.exists(f"{cache_dir}/models--{model_path.replace('/', '--')}"):
    print(f"Model {model_path} found in cache")
else:
    print(f"Model {model_path} not found in cache, downloading...")

pipe = StableDiffusionPipeline.from_pretrained(
    model_path, 
    torch_dtype=torch.float16,
    cache_dir=cache_dir
).to(device)

# Request model
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = None
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512
    return_format: str = "base64"  # Options: base64, file_path

@app.post("/generate")
def generate_image(request: ImageRequest):
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
        
        # Return based on requested format
        if request.return_format == "base64":
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"status": "success", "image": img_str}
        else:
            # Save the image to a file
            os.makedirs("generated_images", exist_ok=True)
            image_path = f"generated_images/{request.prompt.replace(' ', '_')[:30]}.png"
            image.save(image_path)
            return {"status": "success", "image_path": image_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "model": model_path, "device": device}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)