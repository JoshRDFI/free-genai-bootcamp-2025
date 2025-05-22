import chromadb
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import uvicorn
import os
import argparse
from chromadb.config import Settings
from typing import List, Dict, Optional

# Create router with prefix for v2 API
router = APIRouter(prefix="/api/v2")

# Get port from environment variable or default to 8000
port = int(os.getenv("CHROMA_SERVER_PORT", "8000"))

# Initialize ChromaDB client with v2 settings
client = chromadb.HttpClient(
    host="0.0.0.0",
    port=port,
    settings=Settings(
        chroma_api_impl="rest",
        chroma_server_host="0.0.0.0",
        chroma_server_http_port=port
    )
)

class CollectionRequest(BaseModel):
    name: str
    metadata: dict = {}

class DocumentRequest(BaseModel):
    collection_name: str
    documents: list[str]
    metadatas: list[dict] = None
    ids: list[str] = None

@router.get("/collections")
async def get_collections():
    """Get all collections"""
    try:
        collections = client.list_collections()
        return [{"name": col.name, "metadata": col.metadata()} for col in collections]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections")
async def create_collection(request: CollectionRequest):
    """Create a new collection"""
    try:
        collection = client.create_collection(
            name=request.name,
            metadata=request.metadata
        )
        return {"name": collection.name, "metadata": collection.metadata()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections/{collection_name}/add")
async def add_documents(collection_name: str, request: DocumentRequest):
    """Add documents to a collection"""
    try:
        collection = client.get_collection(collection_name)
        collection.add(
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids
        )
        return {"status": "success", "message": "Documents added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections/{collection_name}/query")
async def query_collection(collection_name: str, request: dict):
    """Query a collection"""
    try:
        collection = client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=request.get("query_embeddings", []),
            n_results=request.get("n_results", 5)
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create FastAPI app with title and description
app = FastAPI(
    title="ChromaDB API",
    description="REST API for ChromaDB operations",
    version="2.0.0"
)

# Include router with prefix
app.include_router(router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    port = int(os.getenv("CHROMA_SERVER_PORT", args.port))
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=True) 