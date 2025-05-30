from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import json
from enum import Enum
import asyncio
import shutil
from pathlib import Path
import subprocess
from contextlib import asynccontextmanager

# Constants
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://ollama-server:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
USE_LOCAL = os.getenv("USE_LOCAL", "False").lower() == "true"
OLLAMA_DATA_PATH = os.getenv("OLLAMA_DATA_PATH", "../../data/ollama_data")
MODELS_DATA_PATH = os.path.join(OLLAMA_DATA_PATH, "models")

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
    stream: Optional[bool] = True  # Default to streaming

class ChatResponse(BaseModel):
    model: str
    message: Message
    done: bool

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not USE_LOCAL:
        await ensure_model_exists(DEFAULT_MODEL)
    yield

app = FastAPI(lifespan=lifespan)

def get_model_path(model_name: str) -> Path:
    """Get the path where the model should be stored."""
    return Path(MODELS_DATA_PATH) / "manifests" / "registry.ollama.ai" / "library" / model_name

def model_exists_locally(model_name: str) -> bool:
    """Check if the model exists in local storage."""
    model_path = get_model_path(model_name)
    print(f"Checking for local model at: {model_path}")
    return model_path.exists() and any(model_path.iterdir())

def save_model_locally(model_name: str):
    """Save the model from Ollama to local storage."""
    try:
        # Create necessary directories
        model_path = get_model_path(model_name)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use ollama CLI to save the model
        result = subprocess.run(
            ["ollama", "save", model_name, str(model_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to save model: {result.stderr}")
            
        print(f"Successfully saved model {model_name} to {model_path}")
    except Exception as e:
        print(f"Error saving model locally: {str(e)}")
        raise

def load_model_from_local(model_name: str):
    """Load the model from local storage to Ollama."""
    try:
        model_path = get_model_path(model_name)
        if not model_path.exists():
            raise Exception(f"Model {model_name} not found in local storage")
            
        # Use ollama CLI to load the model
        result = subprocess.run(
            ["ollama", "load", str(model_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to load model: {result.stderr}")
            
        print(f"Successfully loaded model {model_name} from {model_path}")
    except Exception as e:
        print(f"Error loading model from local storage: {str(e)}")
        raise

async def ensure_model_exists(model_name: str):
    """Ensure the model exists, pull it if it doesn't."""
    try:
        # Check if model exists locally first if USE_LOCAL is True
        if USE_LOCAL and model_exists_locally(model_name):
            print(f"Model {model_name} found in local storage")
            load_model_from_local(model_name)
            return

        async with httpx.AsyncClient() as client:
            # Check if model exists in Ollama
            response = await client.get(f"{LLM_ENDPOINT}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if any(m["name"] == model_name for m in models):
                    print(f"Model {model_name} already exists in Ollama")
                    if USE_LOCAL:
                        save_model_locally(model_name)
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

            # Save to local storage if USE_LOCAL is True
            if USE_LOCAL:
                save_model_locally(model_name)

    except Exception as e:
        print(f"Error ensuring model exists: {str(e)}")
        raise

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    try:
        # Format messages for Ollama
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Prepare the request for Ollama
        payload = {
            "model": request.model or DEFAULT_MODEL,
            "messages": ollama_messages,
            "stream": request.stream,  # Use the stream parameter from the request
            "temperature": request.temperature
        }

        # Make request to Ollama
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_ENDPOINT}/api/chat",
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM service error: {response.text}"
                )

            if request.stream:
                # Handle streaming response
                content = ""
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content += chunk["message"]["content"]
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

                if not content:
                    raise HTTPException(
                        status_code=500,
                        detail="No valid response content received from LLM service"
                    )

                return ChatResponse(
                    model=request.model or DEFAULT_MODEL,
                    message=Message(
                        role=Role.ASSISTANT,
                        content=content
                    ),
                    done=True
                )
            else:
                # Handle non-streaming response
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
                return {
                    "status": "healthy", 
                    "ollama_status": "connected", 
                    "default_model": DEFAULT_MODEL,
                    "use_local": USE_LOCAL
                }
            return {"status": "degraded", "ollama_status": "disconnected"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LLM_SERVICE_PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)