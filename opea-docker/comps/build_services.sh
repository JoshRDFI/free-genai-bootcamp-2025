#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists in parent directory
if [ ! -f ../.env ]; then
    print_error "No .env file found in parent directory. Please ensure .env exists in opea-docker/"
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ../../data/{ollama_data,shared_db,llm_xtts,chroma_data,mangaocr_models,tts_data,asr_data,waifu,vocabulary_generator}

# Verify GPU availability
if ! command -v nvidia-smi &> /dev/null; then
    print_warning "nvidia-smi not found. GPU services may not work properly."
else
    print_status "GPU detected. GPU services will be available."
fi

# Build base services first
print_status "Building base services..."
docker compose build ollama-server chromadb

# Build core services
print_status "Building core services..."
docker compose build llm_text embeddings

# Build AI services
print_status "Building AI services..."
docker compose build llm-vision tts asr

# Build utility services
print_status "Building utility services..."
docker compose build guardrails waifu-diffusion vocabulary_generator

# Start all services
print_status "Starting all services..."
docker compose up -d

# Check service status
print_status "Checking service status..."
docker compose ps

print_status "Build and startup complete!"
print_status "You can check individual service logs using: docker compose logs <service-name>"
print_status "Note: Make sure the .env file in the parent directory (opea-docker/.env) is properly configured." 