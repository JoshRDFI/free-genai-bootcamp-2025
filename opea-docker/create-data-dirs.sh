#!/bin/bash

# Create all necessary data directories for opea-docker

# Base data directory
mkdir -p ./app/data

# Service-specific data directories
mkdir -p ./app/data/shared_db
mkdir -p ./app/data/ollama_data
mkdir -p ./app/data/chroma_data
mkdir -p ./app/data/tts_data
mkdir -p ./app/data/asr_data
mkdir -p ./app/data/llm_xtts
mkdir -p ./app/data/mangaocr_models

echo "All data directories created successfully."