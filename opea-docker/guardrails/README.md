# Enhanced Guardrails Service

This service provides robust content filtering and safety guardrails for LLM interactions in a production environment.

## Features

### 1. Sophisticated Content Filtering
- Advanced text analysis using multiple filtering techniques
- Profanity detection with customizable word lists
- Pattern matching for harmful content categories
- Intent analysis using NLP

### 2. Context-Aware Moderation
- Analyzes conversation history to detect policy circumvention attempts
- Identifies escalating harmful patterns across multiple messages
- Prevents prompt injection and jailbreaking attempts

### 3. Rate Limiting
- Redis-backed rate limiting with configurable thresholds
- Sliding window implementation for accurate tracking
- Proper retry-after headers in responses

### 4. Improved Logging
- Structured logging with request IDs for traceability
- Multiple log formats (console, file, JSON)
- Security event logging for compliance and auditing
- Privacy-conscious logging that avoids storing sensitive content

### 5. Configuration Flexibility
- Environment variable configuration
- .env file support
- Per-request guardrail customization

### 6. Multi-Language Support
- Language detection for incoming content
- Configurable list of supported languages
- Language-specific content filtering

### 7. Better Error Handling
- Automatic retries for external service calls
- Graceful degradation when dependencies are unavailable
- Detailed error responses with appropriate status codes

## API Endpoints

### POST /v1/guardrails
Main endpoint for content filtering and LLM interaction.

**Request:**
```json
{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you today?"}
  ],
  "temperature": 0.7,
  "stream": false,
  "guardrails": {
    "content_filter": true,
    "context_moderation": true,
    "rate_limit": true
  }
}
```

**Response:**
```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "I'm doing well, thank you for asking! How can I assist you today?"
  },
  "done": true,
  "filtered": false,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /health
Endpoint for health checks and monitoring.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "llm": "connected",
    "redis": "connected"
  },
  "config": {
    "content_filter_enabled": true,
    "context_moderation_enabled": true,
    "rate_limit_enabled": true,
    "multi_language_enabled": true
  }
}
```

### GET /metrics
Endpoint for monitoring and metrics.

## Configuration

Copy the `.env.example` file to `.env` and adjust the settings as needed:

```
# Service configuration
LOG_LEVEL=INFO

# LLM service configuration
LLM_ENDPOINT=http://llm_text:9000/v1/chat/completions

# Redis configuration for rate limiting
REDIS_HOST=redis
REDIS_PORT=6379

# Content filtering configuration
CONTENT_FILTER_ENABLED=true
# ... and more settings
```

## Running the Service

### Using Docker

```bash
docker build -t guardrails-service .
docker run -p 9400:9400 --env-file .env guardrails-service
```

### Using Docker Compose

The service is included in the main docker-compose.yml file and will be started with the rest of the services.

## Development

### Prerequisites
- Python 3.10+
- Redis (for rate limiting)

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Edit as needed
python -m spacy download en_core_web_sm
```

### Running Locally

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 9400
```