import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI()
client = chromadb.Client()

class CollectionRequest(BaseModel):
    name: str
    metadata: dict = {}

class DocumentRequest(BaseModel):
    collection_name: str
    documents: list[str]
    metadatas: list[dict] = None
    ids: list[str] = None

@app.post("/create_collection")
async def create_collection(request: CollectionRequest):
    try:
        collection = client.create_collection(
            name=request.name,
            metadata=request.metadata
        )
        return {"status": "success", "message": f"Collection {request.name} created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_documents")
async def add_documents(request: DocumentRequest):
    try:
        collection = client.get_collection(request.collection_name)
        collection.add(
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids
        )
        return {"status": "success", "message": "Documents added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_collections")
async def list_collections():
    try:
        collections = client.list_collections()
        return {"collections": [col.name for col in collections]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002) 