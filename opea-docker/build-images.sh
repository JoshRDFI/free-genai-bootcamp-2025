#!/bin/bash

# Function to build a Docker image
build_image() {
    local component=$1
    local image_name=$2
    echo "Building $image_name from $component..."
    docker build -t $image_name:latest ./comps/$component
}

# Build all images
build_image "llm_text" "opea-docker-llm-text"
build_image "guardrails" "opea-docker-guardrails"
build_image "tts" "opea-docker-tts"
build_image "asr" "opea-docker-asr"
build_image "llm-vision" "opea-docker-llm-vision"
build_image "waifu-diffusion" "opea-docker-waifu-diffusion"
build_image "embeddings" "opea-docker-embeddings"
build_image "chromadb" "opea-docker-chromadb"

echo "All images built successfully!" 