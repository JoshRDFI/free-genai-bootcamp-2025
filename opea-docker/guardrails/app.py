import time
import json
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import Field
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union
import httpx
from enum import Enum
import uuid
import os

# Import our custom modules
from config import config
from filters import content_filter
from rate_limiter import rate_limiter
from logger import logger, log_request_response, log_security_event
from utils import generate_request_id, get_client_id, with_retry, safe_get, create_error_response

# Define models
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
    
    class Config:
        schema_extra = {
            "example": {
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you today?"}
                ],
                "temperature": 0.7,
                "stream": False,
                "guardrails": {
                    "content_filter": True,
                    "context_moderation": True,
                    "rate_limit": True
                }
            }
        }

class GuardrailsResponse(BaseModel):
    model: str
    message: Message
    done: bool
    filtered: bool = False
    filter_reason: Optional[str] = None
    request_id: str = Field(default_factory=generate_request_id)

# Initialize FastAPI app
app = FastAPI(
    title="Guardrails Service",
    description="A service that provides content filtering and safety guardrails for LLM interactions",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to add request ID to response headers
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = generate_request_id()
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    
    return response

# Dependency to check rate limits
async def check_rate_limit(request: Request):
    client_id = get_client_id(request)
    request.state.client_id = client_id
    
    # Check if client is rate limited
    is_limited, retry_after = rate_limiter.is_rate_limited(client_id)
    if is_limited:
        log_security_event(
            request_id=request.state.request_id,
            client_id=client_id,
            event_type="RATE_LIMIT_EXCEEDED",
            details=f"Client exceeded rate limit. Retry after {retry_after} seconds."
        )
        
        headers = {"Retry-After": str(retry_after)}
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers=headers
        )
    
    return client_id

# Helper function to create a filtered response
def create_filtered_response(request: GuardrailsRequest, reason: str, request_id: str) -> GuardrailsResponse:
    return GuardrailsResponse(
        model=request.model,
        message=Message(
            role=Role.ASSISTANT,
            content=config.response_templates["content_filtered"]
        ),
        done=True,
        filtered=True,
        filter_reason=reason,
        request_id=request_id
    )

# LLM service call with retry logic
@with_retry
async def call_llm_service(request_data: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.llm_endpoint,
            json=request_data,
            timeout=config.llm_timeout
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from LLM service: {response.text}"
            )
        
        return response.json()

@app.post("/v1/guardrails", response_model=GuardrailsResponse)
async def guardrails_completion(
    request: GuardrailsRequest,
    req: Request,
    client_id: str = Depends(check_rate_limit),
    user_agent: Optional[str] = Header(None)
):
    request_id = req.state.request_id
    start_time = time.time()
    
    try:
        # Log the incoming request (sanitized)
        logger.info(f"Request {request_id} from {client_id}: model={request.model}, messages={len(request.messages)}")
        
        # Extract guardrail settings from request or use defaults
        guardrail_settings = request.guardrails or {}
        content_filter_enabled = guardrail_settings.get("content_filter", config.content_filter_enabled)
        context_moderation_enabled = guardrail_settings.get("context_moderation", config.context_moderation_enabled)
        
        # Apply content filtering to user messages if enabled
        if content_filter_enabled:
            user_messages = [msg for msg in request.messages if msg.role == Role.USER]
            if user_messages:
                # Check the latest user message
                filtered, reason = content_filter.filter_content(user_messages[-1].content)
                if filtered:
                    log_security_event(
                        request_id=request_id,
                        client_id=client_id,
                        event_type="CONTENT_FILTERED",
                        details=f"User content filtered: {reason}"
                    )
                    response = create_filtered_response(request, reason, request_id)
                    
                    # Log the response
                    duration_ms = (time.time() - start_time) * 1000
                    log_request_response(
                        request_id=request_id,
                        client_id=client_id,
                        request_data=request.dict(),
                        response_data=response.dict(),
                        duration_ms=duration_ms
                    )
                    
                    return response
        
        # Apply context moderation if enabled
        if context_moderation_enabled:
            # Convert messages to dict format for the filter
            messages_dict = [msg.dict() for msg in request.messages]
            context_filtered, context_reason = content_filter.analyze_context(messages_dict)
            
            if context_filtered:
                log_security_event(
                    request_id=request_id,
                    client_id=client_id,
                    event_type="CONTEXT_FILTERED",
                    details=f"Conversation context filtered: {context_reason}"
                )
                
                response = GuardrailsResponse(
                    model=request.model,
                    message=Message(
                        role=Role.ASSISTANT,
                        content=config.response_templates["context_violation"]
                    ),
                    done=True,
                    filtered=True,
                    filter_reason=context_reason,
                    request_id=request_id
                )
                
                # Log the response
                duration_ms = (time.time() - start_time) * 1000
                log_request_response(
                    request_id=request_id,
                    client_id=client_id,
                    request_data=request.dict(),
                    response_data=response.dict(),
                    duration_ms=duration_ms
                )
                
                return response
        
        # If not filtered, forward to LLM service
        llm_request = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "temperature": request.temperature,
            "stream": False  # Force stream to False for now
        }
        
        # Call LLM service with retry logic
        result = await call_llm_service(llm_request)
        
        # Check if LLM response needs filtering
        llm_content = safe_get(result, "message.content", "")
        if content_filter_enabled and llm_content:
            filtered, reason = content_filter.filter_content(llm_content)
            if filtered:
                log_security_event(
                    request_id=request_id,
                    client_id=client_id,
                    event_type="LLM_CONTENT_FILTERED",
                    details=f"LLM response filtered: {reason}"
                )
                
                response = create_filtered_response(request, reason, request_id)
                
                # Log the response
                duration_ms = (time.time() - start_time) * 1000
                log_request_response(
                    request_id=request_id,
                    client_id=client_id,
                    request_data=request.dict(),
                    response_data=response.dict(),
                    duration_ms=duration_ms
                )
                
                return response
        
        # Return the unfiltered response
        response = GuardrailsResponse(
            model=result.get("model", request.model),
            message=Message(
                role=Role.ASSISTANT,
                content=safe_get(result, "message.content", "")
            ),
            done=True,
            filtered=False,
            request_id=request_id
        )
        
        # Log the successful response
        duration_ms = (time.time() - start_time) * 1000
        log_request_response(
            request_id=request_id,
            client_id=client_id,
            request_data=request.dict(),
            response_data=response.dict(),
            duration_ms=duration_ms
        )
        
        return response
    
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log the error
        logger.exception(f"Error processing request {request_id}: {str(e)}")
        
        # Return a generic error response
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message="An error occurred while processing your request",
                details=str(e) if config.log_level == "DEBUG" else None
            )
        )

@app.get("/health")
async def health_check(request: Request):
    try:
        # Check if LLM service is responsive
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.llm_endpoint.split('/v1')[0]}/health",
                timeout=5.0
            )
            llm_status = "connected" if response.status_code == 200 else "disconnected"
    except Exception as e:
        llm_status = f"error: {str(e)}"
    
    # Check if Redis is connected (for rate limiting)
    redis_status = "connected" if rate_limiter.redis_client else "disconnected"
    
    health_data = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "llm": llm_status,
            "redis": redis_status
        },
        "config": {
            "content_filter_enabled": config.content_filter_enabled,
            "context_moderation_enabled": config.context_moderation_enabled,
            "rate_limit_enabled": config.rate_limit_enabled,
            "multi_language_enabled": config.multi_language_enabled
        }
    }
    
    return health_data

@app.get("/metrics")
async def metrics(request: Request):
    """Endpoint for monitoring and metrics."""
    # This would typically integrate with a metrics system like Prometheus
    # For now, we'll return some basic stats
    return {
        "uptime": "unknown",  # Would track service uptime
        "requests_processed": "unknown",  # Would track total requests
        "requests_filtered": "unknown",  # Would track filtered requests
        "average_response_time_ms": "unknown"  # Would track response times
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the exception
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            status_code=500,
            message="An unexpected error occurred",
            details=str(exc) if config.log_level == "DEBUG" else None
        )
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GUARDRAILS_SERVICE_PORT", 9400))
    uvicorn.run(app, host="0.0.0.0", port=port)