import sys
import json
from loguru import logger
from config import config

# Configure Loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format=config.log_format,
    level=config.log_level,
    serialize=False,  # Set to True for JSON logging
    backtrace=True,
    diagnose=True,
)

# Add a file handler for persistent logs
logger.add(
    "logs/guardrails.log",
    rotation="10 MB",  # Rotate when file reaches 10MB
    retention="1 week",  # Keep logs for 1 week
    compression="zip",  # Compress rotated logs
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level=config.log_level,
    backtrace=True,
    diagnose=True,
)

# Add a JSON file handler for structured logging (useful for log analysis tools)
logger.add(
    "logs/guardrails.json",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    serialize=True,  # JSON format
    level=config.log_level,
)

# Custom log function for request/response logging
def log_request_response(request_id: str, client_id: str, request_data: dict, response_data: dict, duration_ms: float):
    """Log request and response data in a structured format."""
    log_data = {
        "request_id": request_id,
        "client_id": client_id,
        "duration_ms": duration_ms,
        "request": {
            "model": request_data.get("model"),
            "message_count": len(request_data.get("messages", [])),
            # Don't log the actual messages for privacy
            "has_guardrails": request_data.get("guardrails") is not None,
        },
        "response": {
            "filtered": response_data.get("filtered", False),
            "filter_reason": response_data.get("filter_reason"),
            "done": response_data.get("done", False),
        }
    }
    
    logger.info(f"Request processed: {json.dumps(log_data)}")

# Function to log security events
def log_security_event(request_id: str, client_id: str, event_type: str, details: str):
    """Log security-related events."""
    log_data = {
        "request_id": request_id,
        "client_id": client_id,
        "event_type": event_type,
        "details": details,
    }
    
    logger.warning(f"Security event: {json.dumps(log_data)}")