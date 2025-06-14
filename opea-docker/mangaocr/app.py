from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from PIL import Image
import io

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Helper functions
def get_manga_ocr():
    global _manga_ocr
    if _manga_ocr is None:
        try:
            # Check if we should force CPU usage
            force_cpu = os.getenv('FORCE_CPU', 'false').lower() == 'true'
            
            if force_cpu:
                print("Forcing CPU usage for MangaOCR")
                _manga_ocr = MangaOcr(force_cpu=True)
            else:
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
            return None
        
# Debug: log the MangaOcr object
    print(f"MangaOCR object: {_manga_ocr}")
    return _manga_ocr

def validate_image(image: Image.Image) -> None:
    """Validate image format and size."""
    # Check image format
    if image.format not in ['PNG', 'JPEG', 'JPG']:
        raise HTTPException(status_code=400, detail="Unsupported image format. Please use PNG or JPEG.")
    
    # Check image size
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image.tobytes()) > max_size:
        raise HTTPException(status_code=400, detail="Image size too large. Maximum size is 10MB.")
    
    # Check image dimensions
    max_dimension = 4096
    if image.width > max_dimension or image.height > max_dimension:
        raise HTTPException(status_code=400, detail=f"Image dimensions too large. Maximum dimension is {max_dimension}px.")

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...), language: Optional[str] = Form("ja")):
    try:
        if not manga_ocr_available:
            raise HTTPException(status_code=503, detail="MangaOCR service is not available")
            
        ocr = get_manga_ocr()
        if ocr is None:
            raise HTTPException(status_code=503, detail="MangaOCR service failed to initialize")

        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read the uploaded file
        contents = await file.read()
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(contents))
            image.load()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # Validate image
        validate_image(image)
        
        # Process with MangaOCR using the PIL Image
        try:
            text = ocr(image)
            if not text:
                raise HTTPException(status_code=422, detail="No text could be extracted from the image")
            return {"text": text, "language": language}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image with OCR: {str(e)}")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        # Check MangaOCR status
        manga_ocr_status = "available" if manga_ocr_available else "not available"
        if manga_ocr_available:
            ocr = get_manga_ocr()
            manga_ocr_status = "initialized" if ocr is not None else "not initialized"
            
        return {
            "status": "healthy", 
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
    port = int(os.getenv("MANGAOCR_PORT", 9100))
    uvicorn.run(app, host="0.0.0.0", port=port)