# OPEA Docker Microservices

This repository contains a set of microservices for the OPEA (Open Platform for Educational AI) system. The services are designed to work together to provide a comprehensive AI platform for educational applications.

## Services

1. **LLM Text Service**: Text-based large language model service using Ollama
2. **Embeddings Service**: Text embedding service for semantic search and similarity
3. **LLM Vision Service**: Vision-language model service for image understanding
4. **TTS Service**: Text-to-Speech service for audio generation
5. **ASR Service**: Automatic Speech Recognition service for transcription
6. **ChromaDB**: Vector database for storing and retrieving embeddings
7. **Guardrails Service**: Content filtering and safety service

## Getting Started

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (optional but recommended)
- NVIDIA Container Toolkit (if using GPU)

### Setup

1. Create the necessary data directories:

```bash
./create-data-dirs.sh
```

2. Configure environment variables in the `.env` file

3. Start the services:

```bash
docker-compose up -d
```

### TTS Service Setup

Before starting the TTS service, you need to download the XTTS v2 model files:

1. Install the setup requirements:
   ```bash
   pip install -r setup_requirements.txt
   ```

2. Run the setup script:
   ```bash
   python setup_tts.py
   ```

This will download the required model files to `./data/tts_data/`. The files will be automatically mounted into the TTS service container.

### Starting Services

After setting up the TTS service, you can start all services:

```bash
docker compose up -d
```

## Service Endpoints

- LLM Text Service: http://localhost:9000/v1/chat/completions
- Embeddings Service: http://localhost:6000/embed
- LLM Vision Service: http://localhost:9100/v1/vision
- TTS Service: http://localhost:9200/tts
- ASR Service: http://localhost:9300/asr
- ChromaDB: http://localhost:8050
- Guardrails Service: http://localhost:9400/v1/guardrails

## Health Checks

Each service provides a health check endpoint at `/health`.

## Development

To develop or extend the services:

1. Modify the service code in the respective directory
2. Rebuild and restart the service:

```bash
docker-compose up -d --build <service_name>
```

## Using the opea-comps Package

The `opea-comps` package provides utilities for service orchestration and communication. To install it:

```bash
cd opea-comps
pip install -e .
```

Example usage:

```python
from opea-comps import MicroService, ServiceOrchestrator, ServiceType

# Create a service orchestrator
orchestrator = ServiceOrchestrator()

# Add services
llm = MicroService(name="llm", host="localhost", port=9000, endpoint="/v1/chat/completions")
embeddings = MicroService(name="embeddings", host="localhost", port=6000, endpoint="/embed")

# Define flow
orchestrator.add(llm).add(embeddings)
orchestrator.flow_to(embeddings, llm)

# Process data
result = orchestrator.process("embeddings", {"texts": ["Hello, world!"]})
```