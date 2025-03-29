#!/bin/bash

# Create necessary data directories
./create-data-dirs.sh

# Build the Docker images
docker compose build

# Start the containers
docker compose up -d

echo "OPEA services started. Use 'docker compose logs -f' to view logs."
echo "Service endpoints:"
echo "- LLM Text Service: http://localhost:9000/v1/chat/completions"
echo "- Embeddings Service: http://localhost:6000/embed"
echo "- LLM Vision Service: http://localhost:9100/v1/vision"
echo "- TTS Service: http://localhost:9200/tts"
echo "- ASR Service: http://localhost:9300/asr"
echo "- ChromaDB: http://localhost:8050"
echo "- Guardrails Service: http://localhost:9400/v1/guardrails"