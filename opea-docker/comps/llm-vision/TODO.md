# Vision Service Enhancement: Adding LLaVA Support

## Overview
This document outlines the necessary changes to add LLaVA (Large Language and Vision Assistant) support to the vision service while maintaining existing MangaOCR functionality.

## Current Architecture
- Port: 9100
- Current Features:
  - MangaOCR for Japanese text recognition
  - Image analysis capabilities

## Required Changes

### 1. Docker Container Updates
```dockerfile
# Add to Dockerfile
RUN pip install transformers torch torchvision
RUN pip install git+https://github.com/haotian-liu/LLaVA.git

# Create model directories
RUN mkdir -p /app/data/llava_models
RUN mkdir -p /app/data/mangaocr_models

# Download LLaVA model to persistent storage
RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
    AutoTokenizer.from_pretrained('liuhaotian/llava-v1.5-13b', cache_dir='/app/data/llava_models'); \
    AutoModelForCausalLM.from_pretrained('liuhaotian/llava-v1.5-13b', cache_dir='/app/data/llava_models')"
```

Update docker-compose.yml to include volume mounts:
```yaml
llm-vision:
  build:
    context: ./llm-vision
    dockerfile: Dockerfile
  volumes:
    - ../data/llava_models:/app/data/llava_models
    - ../data/mangaocr_models:/app/data/mangaocr_models
  environment:
    - TRANSFORMERS_CACHE=/app/data/llava_models
    - MANGAOCR_MODEL_PATH=/app/data/mangaocr_models
```

### 2. Service Configuration
Update `app.py` to include LLaVA endpoints:
```python
from transformers import AutoProcessor, LlavaForConditionalGeneration
import torch
import os

class VisionService:
    def __init__(self):
        # Get model paths from environment
        llava_model_path = os.getenv("TRANSFORMERS_CACHE", "/app/data/llava_models")
        mangaocr_model_path = os.getenv("MANGAOCR_MODEL_PATH", "/app/data/mangaocr_models")
        
        self.manga_ocr = MangaOcr()  # Existing MangaOCR
        self.llava_processor = AutoProcessor.from_pretrained(
            "liuhaotian/llava-v1.5-13b",
            cache_dir=llava_model_path
        )
        self.llava_model = LlavaForConditionalGeneration.from_pretrained(
            "liuhaotian/llava-v1.5-13b",
            cache_dir=llava_model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    @app.post("/analyze_image")
    async def analyze_image(
        file: UploadFile = File(...),
        prompt: str = Form("What's in this image?")
    ):
        # LLaVA image analysis endpoint
        pass

    @app.post("/ocr")
    async def ocr_image(
        file: UploadFile = File(...),
        language: str = Form("ja")
    ):
        # Existing MangaOCR endpoint
        pass
```

### 3. Resource Requirements
- GPU Memory: Minimum 16GB recommended for LLaVA
- Storage: Additional ~13GB for LLaVA model
- RAM: Minimum 32GB recommended
- Persistent Storage:
  - LLaVA models: ~13GB
  - MangaOCR models: ~500MB
  - Total recommended: 20GB

### 4. Environment Variables
Add to `.env`:
```env
LLAVA_MODEL_ID=liuhaotian/llava-v1.5-13b
LLAVA_DEVICE=cuda
TRANSFORMERS_CACHE=/app/data/llava_models
MANGAOCR_MODEL_PATH=/app/data/mangaocr_models
```

### 5. API Documentation Updates
Add new endpoint documentation:
```markdown
## Vision Service API

### POST /analyze_image
Analyze image content using LLaVA.

Parameters:
- file: Image file (multipart/form-data)
- prompt: Analysis prompt (optional)

Response:
```json
{
    "analysis": "string",
    "confidence": float
}
```

### POST /ocr
Extract text from image using MangaOCR.

Parameters:
- file: Image file (multipart/form-data)
- language: Language code (default: "ja")

Response:
```json
{
    "text": "string",
    "language": "string"
}
```
```

## Implementation Steps

1. **Docker Updates**
   - [ ] Update Dockerfile with LLaVA dependencies
   - [ ] Add model download step
   - [ ] Update resource limits in docker-compose.yml
   - [ ] Configure persistent storage volumes
   - [ ] Set up model caching directories

2. **Service Updates**
   - [ ] Add LLaVA model initialization
   - [ ] Implement new /analyze_image endpoint
   - [ ] Add error handling for GPU memory issues
   - [ ] Implement graceful fallback to CPU if needed
   - [ ] Configure model loading from persistent storage

3. **Testing**
   - [ ] Test LLaVA image analysis
   - [ ] Verify MangaOCR still works
   - [ ] Test concurrent usage of both services
   - [ ] Performance testing under load
   - [ ] Verify model persistence across container restarts

4. **Documentation**
   - [ ] Update API documentation
   - [ ] Add usage examples
   - [ ] Document resource requirements
   - [ ] Add troubleshooting guide
   - [ ] Document storage requirements and persistence

## Notes
- LLaVA model is large (~13GB), consider implementing lazy loading
- May need to implement model quantization for lower memory usage
- Consider adding a model cache to improve startup time
- Monitor GPU memory usage during concurrent requests
- Ensure proper permissions on persistent storage directories
- Consider implementing model versioning in storage paths

## Future Enhancements
- Add support for multiple LLaVA model variants
- Implement batch processing for multiple images
- Add support for video analysis
- Implement model versioning and updates
- Add model cleanup and maintenance utilities 