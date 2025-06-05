#!/bin/bash

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    export DOCKER_RUNTIME=nvidia
    export GPU_DRIVER=nvidia
    export GPU_COUNT=all
    export FORCE_CPU=false
else
    echo "No NVIDIA GPU detected, running in CPU mode"
    export DOCKER_RUNTIME=runc
    export GPU_DRIVER=none
    export GPU_COUNT=0
    export FORCE_CPU=true
fi

# Create necessary data directories
./create-data-dirs.sh

# Build the Docker images
echo "Building Docker images..."
docker compose build

# Start the containers one by one for clear output
echo "Starting ollama-server..."
docker compose up -d ollama-server

echo "Starting llm_text..."
docker compose up -d llm_text

echo "Starting guardrails..."
docker compose up -d guardrails

echo "Starting chromadb..."
docker compose up -d chromadb

echo "Starting tts..."
docker compose up -d tts

echo "Starting asr..."
docker compose up -d asr

echo "Starting llm-vision..."
docker compose up -d llm-vision

echo "Starting waifu-diffusion..."
docker compose up -d waifu-diffusion

echo "Starting embeddings..."
docker compose up -d embeddings

echo "OPEA services started. Use 'docker compose logs -f' to view logs."
echo "Service endpoints:"
echo "- LLM Text Service: http://localhost:9000/v1/chat/completions"
echo "- Embeddings Service: http://localhost:6000/embed"
echo "- LLM Vision Service: http://localhost:9100/v1/vision"
echo "- TTS Service: http://localhost:9200/tts"
echo "- ASR Service: http://localhost:9300/asr"
echo "- ChromaDB: http://localhost:8050"
echo "- Guardrails Service: http://localhost:9400/v1/guardrails"
echo "- Waifu Diffusion: http://localhost:9500/generate"