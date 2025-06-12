from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from enum import Enum

# Constants
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://ollama-server:11434")

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: Role
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    model: str
    message: Message
    done: bool

# Initialize FastAPI app
app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    try:
        # Format messages for Ollama
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Prepare the request for Ollama
        ollama_request = {
            "model": request.model,
            "messages": ollama_messages,
            "stream": False,
            "temperature": request.temperature
        }

        # Make request to Ollama
        async with httpx.AsyncClient() as client:
            # First, ensure the model is pulled
            try:
                await client.post(
                    f"{LLM_ENDPOINT}/api/pull",
                    json={"name": request.model},
                    timeout=120.0  # Increased from 30.0 to handle larger models
                )
            except Exception as e:
                print(f"Warning: Model pull failed: {e}")

            # Make the generation request
            response = await client.post(
                f"{LLM_ENDPOINT}/api/generate",  # or use /api/chat for newer Ollama versions
                json=ollama_request,
                timeout=180.0  # Increased from 60.0 for longer responses
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error from LLM service: {response.text}"
                )

            result = response.json()

            # Handle different response formats
            content = ""
            if "response" in result:  # Ollama generate API
                content = result["response"]
            elif "message" in result:  # Ollama chat API
                content = result["message"]["content"]

            return ChatResponse(
                model=request.model,
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
                return {"status": "healthy", "ollama_status": "connected"}
            return {"status": "healthy", "ollama_status": "disconnected"}
    except Exception as e:
        return {"status": "healthy", "ollama_status": f"error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)