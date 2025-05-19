#!/bin/bash

# Function to build a Docker image
build_image() {
    local component=$1
    local image_name=$2
    echo "Building $image_name from $component..."
    docker build --no-cache -t $image_name:latest ./comps/$component
    if [ $? -eq 0 ]; then
        echo "Successfully built $image_name"
    else
        echo "Failed to build $image_name"
        exit 1
    fi
}

# Build all images
echo "Starting Docker image builds..."
build_image "llm_text" "opea-docker-llm-text"
build_image "guardrails" "opea-docker-guardrails"
build_image "tts" "opea-docker-tts"
build_image "asr" "opea-docker-asr"
build_image "llm-vision" "opea-docker-llm-vision"
build_image "waifu-diffusion" "opea-docker-waifu-diffusion"
build_image "embeddings" "opea-docker-embeddings"
build_image "chromadb" "opea-docker-chromadb"

echo "All images built successfully!" 