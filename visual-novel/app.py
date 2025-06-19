from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import base64
from io import BytesIO
from PIL import Image

# Initialize FastAPI app
app = FastAPI(title="Visual Novel API Gateway", description="API Gateway for Visual Novel services")

# Service URLs from environment variables (set by Docker)
WAIFU_DIFFUSION_URL = os.environ.get("WAIFU_DIFFUSION_URL", "http://localhost:9500")
GAME_SERVER_URL = os.environ.get("GAME_SERVER_URL", "http://localhost:8080")
LLM_URL = os.environ.get("LLM_TEXT_URL", "http://localhost:11434")
TTS_URL = os.environ.get("TTS_URL", "http://localhost:9200")

# Request model for image generation
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = None
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512
    return_format: str = "base64"  # Options: base64, file_path

@app.post("/generate-image")
def generate_image(request: ImageRequest):
    """Generate image using the waifu-diffusion Docker service"""
    try:
        # Forward request to waifu-diffusion service
        response = requests.post(
            f"{WAIFU_DIFFUSION_URL}/generate",
            json=request.dict(),
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Image generation service error: {str(e)}")

@app.get("/health")
def health_check():
    """Check health of all services"""
    services = {
        "waifu-diffusion": WAIFU_DIFFUSION_URL,
        "game-server": GAME_SERVER_URL,
        "llm": LLM_URL,
        "tts": TTS_URL
    }
    
    health_status = {}
    for service_name, service_url in services.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            health_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": service_url
            }
        except requests.exceptions.RequestException:
            health_status[service_name] = {
                "status": "unreachable",
                "url": service_url
            }
    
    return {
        "status": "ok",
        "services": health_status,
        "message": "Visual Novel API Gateway is running"
    }

@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "message": "Visual Novel API Gateway",
        "services": {
            "image_generation": f"{WAIFU_DIFFUSION_URL}/generate",
            "game_server": GAME_SERVER_URL,
            "health_check": "/health"
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Visual Novel API Gateway...")
    print(f"Waifu Diffusion URL: {WAIFU_DIFFUSION_URL}")
    print(f"Game Server URL: {GAME_SERVER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=5000)