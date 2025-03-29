from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "llm-vision healthy"})

@app.post("/process_image")
async def process_image(payload: dict):
    # Placeholder logic for image processing with MangaOCR
    return JSONResponse({"message": "Image processed", "input": payload})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9100)