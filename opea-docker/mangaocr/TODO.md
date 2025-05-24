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


# Model information for Llava-v1.6-mistral-7b
## Model inputs and outputs
The llava-v1.6-mistral-7b model can process text prompts and images as inputs, and generate text responses. The text prompts can include instructions or questions related to the input image, and the model will attempt to generate a relevant and coherent response.

## Inputs
Image: An image file provided as a URL.
Prompt: A text prompt that includes instructions or a question related to the input image.
History: A list of previous messages in a conversation, alternating between user inputs and model responses, with the image specified in the appropriate message.
Temperature: A value between 0 and 1 that controls the randomness of the model's text generation, with lower values producing more deterministic outputs.
Top P: A value between 0 and 1 that controls how many of the most likely tokens are considered during text generation, with lower values ignoring less likely tokens.
Max Tokens: The maximum number of tokens (words) the model should generate in its response.

## Outputs
Text: The model's generated response to the input prompt and image.

## Capabilities
The llava-v1.6-mistral-7b model is capable of understanding and interpreting visual information in the context of textual prompts, and generating relevant and coherent responses. It can be used for a variety of multimodal tasks, such as image captioning, visual question answering, and image-guided text generation.

## What can I use it for?
The llava-v1.6-mistral-7b model can be a powerful tool for building multimodal applications that combine language and vision, such as:

Interactive image-based chatbots that can answer questions and provide information about the contents of an image
Intelligent image-to-text generation systems that can generate detailed captions or stories based on visual inputs
Visual assistance tools that can help users understand and interact with images and visual content
Multimodal educational or training applications that leverage visual and textual information to teach or explain concepts

## Things to try
With the llava-v1.6-mistral-7b model, you can experiment with a variety of prompts and image inputs to see the model's capabilities in action. Try providing the model with images of different subjects and scenes, and see how it responds to prompts related to the visual content. You can also explore the model's ability to follow instructions and perform tasks by including specific commands in the text prompt.