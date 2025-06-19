#!/bin/bash

# Set error handling
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if virtual environment exists
if [ ! -d ".venv-main" ]; then
    log "Error: Virtual environment not found. Please run first_start.py first:"
    log "python3 first_start.py"
    exit 1
fi

# Check if virtual environment Python exists
if [ ! -f ".venv-main/bin/python" ]; then
    log "Error: Virtual environment Python not found. Please run first_start.py again."
    exit 1
fi

# Activate virtual environment
log "Activating virtual environment..."
source .venv-main/bin/activate

# Check if we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    log "Error: Failed to activate virtual environment"
    exit 1
fi

log "Virtual environment activated: $VIRTUAL_ENV"

# Download models if needed
log "Checking and downloading models..."
python3 download_models.py

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    log "Error: Streamlit not found in virtual environment. Please run first_start.py again."
    exit 1
fi

# Run the project
log "Starting Streamlit application..."
log "The application will be available at: http://localhost:8501"
log "Press Ctrl+C to stop the application"

# Run streamlit with proper error handling
python3 -m streamlit run project_start.py --server.port 8501 --server.address localhost 