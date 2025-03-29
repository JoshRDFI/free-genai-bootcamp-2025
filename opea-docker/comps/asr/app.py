from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "asr healthy"})

@app.post("/transcribe")
async def transcribe_audio(payload: dict):
    # Placeholder logic for automatic speech recognition
    return JSONResponse({"message": "Audio transcribed", "input": payload})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9300)