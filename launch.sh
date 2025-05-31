#!/bin/bash

# Check if virtual environment exists
if [ ! -d ".venv-main" ]; then
    echo "Error: Virtual environment not found. Please run first_start.py first:"
    echo "python3 first_start.py"
    exit 1
fi

# Activate virtual environment and run the script
source .venv-main/bin/activate
python3 download_models.py
streamlit run project_start.py 