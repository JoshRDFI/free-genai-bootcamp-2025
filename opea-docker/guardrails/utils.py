import time
import uuid
from typing import Callable, Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fastapi import Request, HTTPException
from config import config
from logger import logger

# Generate a unique request ID
def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return str(uuid.uuid4())

# Extract client ID from request (e.g., IP address)
def get_client_id(request: Request) -> str:
    """Extract a client identifier from the request."""
    # Get client IP, considering potential proxies
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_id = forwarded.split(",")[0].strip()
    else:
        client_id = request.client.host if request.client else "unknown"
        
    return client_id

# Retry decorator for external service calls
def with_retry(func: Callable) -> Callable:
    """Decorator to add retry logic to functions."""
    @retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=config.retry_backoff, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}. Retrying...")
            raise
    
    return wrapper

# Function to safely access nested dictionary keys
def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely access nested dictionary keys using dot notation."""
    keys = path.split('.')
    result = data
    
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    
    return result

# Function to sanitize user input for logging
def sanitize_for_log(text: str, max_length: int = 100) -> str:
    """Sanitize and truncate text for logging purposes."""
    if not text:
        return ""
        
    # Truncate if too long
    if len(text) > max_length:
        return text[:max_length] + "..."
        
    return text

# Function to create standardized error responses
def create_error_response(status_code: int, message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "error": {
            "status_code": status_code,
            "message": message,
        }
    }
    
    if details:
        response["error"]["details"] = details
        
    return response