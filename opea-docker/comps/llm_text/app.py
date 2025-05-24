from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from enum import Enum
import asyncio

# Constants
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://ollama-server:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
USE_LOCAL = os.getenv("USE_LOCAL", "False").lower() == "true"

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: Role
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = DEFAULT_MODEL
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    model: str
    message: Message
    done: bool

# Initialize FastAPI app
app = FastAPI()

async def ensure_model_exists(model_name: str):
    """Ensure the model exists, pull it if it doesn't."""
    try:
        async with httpx.AsyncClient() as client:
            # Check if model exists
            response = await client.get(f"{LLM_ENDPOINT}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if any(m["name"] == model_name for m in models):
                    print(f"Model {model_name} already exists")
                    return

            # Pull the model if it doesn't exist
            print(f"Pulling model {model_name}...")
            pull_response = await client.post(
                f"{LLM_ENDPOINT}/api/pull",
                json={"name": model_name}
            )
            if pull_response.status_code != 200:
                raise Exception(f"Failed to pull model: {pull_response.text}")
            print(f"Successfully pulled model {model_name}")
    except Exception as e:
        print(f"Error ensuring model exists: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Ensure the default model exists on startup."""
    if not USE_LOCAL:
        await ensure_model_exists(DEFAULT_MODEL)

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    try:
        # Format messages for Ollama
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Prepare the request for Ollama
        payload = {
            "model": request.model or DEFAULT_MODEL,
            "messages": ollama_messages,
            "stream": False,
            "temperature": request.temperature
        }

        # Make request to Ollama
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_ENDPOINT}/api/chat",  # Using chat API for newer Ollama versions
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM service error: {response.text}"
                )

            result = response.json()

            # Handle different response formats
            if "message" in result:  # Ollama chat API
                content = result["message"]["content"]
            elif "response" in result:  # Ollama generate API (fallback)
                content = result["response"]
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected response format from LLM service: {result}"
                )

            return ChatResponse(
                model=request.model or DEFAULT_MODEL,
                message=Message(
                    role=Role.ASSISTANT,
                    content=content
                ),
                done=True
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    try:
        # Check if Ollama server is responsive
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_ENDPOINT}/api/version")
            if response.status_code == 200:
                return {"status": "healthy", "ollama_status": "connected", "default_model": DEFAULT_MODEL}
            return {"status": "degraded", "ollama_status": "disconnected"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LLM_SERVICE_PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)