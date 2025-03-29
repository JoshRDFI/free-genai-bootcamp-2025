from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
from enum import Enum

# Constants
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://llm_text:9000/v1/chat/completions")

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: Role
    content: str

class GuardrailsRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    guardrails: Optional[Dict[str, Any]] = None

class GuardrailsResponse(BaseModel):
    model: str
    message: Message
    done: bool
    filtered: bool = False
    filter_reason: Optional[str] = None

# Initialize FastAPI app
app = FastAPI()

# Simple content filter function
def filter_content(text: str) -> (bool, str):
    # This is a very basic filter - in a real implementation, you would use more sophisticated methods
    forbidden_words = ["hate", "violence", "illegal", "harmful"]
    
    for word in forbidden_words:
        if word in text.lower():
            return True, f"Content contains forbidden word: {word}"
    
    return False, ""

@app.post("/v1/guardrails")
async def guardrails_completion(request: GuardrailsRequest):
    try:
        # Check if user input needs filtering
        user_messages = [msg for msg in request.messages if msg.role == Role.USER]
        if user_messages:
            filtered, reason = filter_content(user_messages[-1].content)
            if filtered:
                return GuardrailsResponse(
                    model=request.model,
                    message=Message(
                        role=Role.ASSISTANT,
                        content="I'm sorry, but I cannot respond to that request as it may contain inappropriate content."
                    ),
                    done=True,
                    filtered=True,
                    filter_reason=reason
                )
        
        # If not filtered, forward to LLM service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LLM_ENDPOINT,
                json={
                    "model": request.model,
                    "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
                    "temperature": request.temperature,
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error from LLM service: {response.text}"
                )
            
            result = response.json()
            
            # Check if LLM response needs filtering
            if "message" in result and "content" in result["message"]:
                filtered, reason = filter_content(result["message"]["content"])
                if filtered:
                    return GuardrailsResponse(
                        model=request.model,
                        message=Message(
                            role=Role.ASSISTANT,
                            content="I apologize, but I cannot provide the generated response as it may contain inappropriate content."
                        ),
                        done=True,
                        filtered=True,
                        filter_reason=reason
                    )
            
            # Return the unfiltered response
            return GuardrailsResponse(
                model=result.get("model", request.model),
                message=Message(
                    role=Role.ASSISTANT,
                    content=result["message"]["content"]
                ),
                done=True,
                filtered=False
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    try:
        # Check if LLM service is responsive
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_ENDPOINT.split('/v1')[0]}/health")
            if response.status_code == 200:
                return {"status": "healthy", "llm_status": "connected"}
            return {"status": "healthy", "llm_status": "disconnected"}
    except Exception as e:
        return {"status": "healthy", "llm_status": f"error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9400)