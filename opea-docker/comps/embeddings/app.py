from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from sentence_transformers import SentenceTransformer

# Constants
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Initialize FastAPI app
app = FastAPI()

# Load the embedding model
model = None

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

@app.on_event("startup")
async def startup_event():
    global model
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"Loaded embedding model: {EMBEDDING_MODEL}")
    except Exception as e:
        print(f"Error loading embedding model: {e}")

@app.post("/embed")
async def create_embeddings(request: EmbeddingRequest):
    global model
    if model is None:
        raise HTTPException(status_code=500, detail="Embedding model not loaded")
    
    try:
        # Generate embeddings
        embeddings = model.encode(request.texts).tolist()
        return EmbeddingResponse(embeddings=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@app.get("/health")
async def health_check():
    global model
    return {"status": "healthy", "model": EMBEDDING_MODEL, "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)