#!/bin/bash

# Create all necessary data directories for opea-docker

# Base data directory
mkdir -p ./data

# Service-specific data directories
mkdir -p ./data/shared_db
mkdir -p ./data/ollama_data
mkdir -p ./data/chroma_data
mkdir -p ./data/tts_data
mkdir -p ./data/asr_data
mkdir -p ./data/llm_xtts
mkdir -p ./data/mangaocr_models

echo "All data directories created successfully."