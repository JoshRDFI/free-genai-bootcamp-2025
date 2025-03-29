from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "embeddings healthy"})

@app.post("/embed")
async def embed_text(payload: dict):
    # Placeholder logic for text embeddings
    return JSONResponse({"message": "Embedding computed", "input": payload})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)