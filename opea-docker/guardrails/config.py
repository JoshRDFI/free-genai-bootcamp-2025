import os
from typing import List, Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class GuardrailsConfig(BaseSettings):
    # Service configuration
    service_name: str = "guardrails"
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", env="LOG_FORMAT")
    
    # LLM service configuration
    llm_endpoint: str = Field(default="http://localhost:11434/api/chat", env="LLM_ENDPOINT")
    model: str = Field(default="llama3.2", env="MODEL")
    llm_timeout: float = Field(default=180.0, env="LLM_TIMEOUT")
    
    # Redis configuration for rate limiting
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Rate limiting configuration
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")  # Number of requests
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # Period in seconds
    
    # Content filtering configuration
    content_filter_enabled: bool = Field(default=True, env="CONTENT_FILTER_ENABLED")
    forbidden_words: List[str] = Field(
        default=[
            "hate", "violence", "illegal", "harmful", "racist", "sexist", 
            "discriminatory", "offensive", "explicit", "pornographic"
        ],
        env="FORBIDDEN_WORDS"
    )
    
    # Context-aware moderation configuration
    context_moderation_enabled: bool = Field(default=True, env="CONTEXT_MODERATION_ENABLED")
    max_context_length: int = Field(default=10, env="MAX_CONTEXT_LENGTH")  # Number of messages to consider for context
    
    # Multi-language support
    multi_language_enabled: bool = Field(default=True, env="MULTI_LANGUAGE_ENABLED")
    supported_languages: List[str] = Field(
        default=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar"],
        env="SUPPORTED_LANGUAGES"
    )
    
    # Error handling configuration
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_backoff: float = Field(default=1.0, env="RETRY_BACKOFF")
    
    # Response templates
    response_templates: Dict[str, str] = {
        "content_filtered": "I'm sorry, but I cannot respond to that request as it may contain inappropriate content.",
        "rate_limited": "You have exceeded the allowed number of requests. Please try again later.",
        "language_not_supported": "I'm sorry, but I don't currently support that language.",
        "error": "An error occurred while processing your request. Please try again later.",
        "context_violation": "I'm sorry, but the conversation context appears to be attempting to circumvent safety guidelines."
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global config instance
config = GuardrailsConfig()