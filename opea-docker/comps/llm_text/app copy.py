from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "llm_text healthy"})

@app.post("/process")
async def process_text(payload: dict):
    # Placeholder logic for LLM text processing
    return JSONResponse({"message": "Text processed", "input": payload})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)