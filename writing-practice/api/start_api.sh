#!/bin/bash

# Determine which Python command to use (python or python3)
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed or not in your PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    
    # If venv creation fails, try using the system's virtualenv command
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment with venv module"
        echo "Trying with virtualenv command..."
        
        if command -v virtualenv &>/dev/null; then
            virtualenv venv
        else
            echo "Error: Could not create virtual environment"
            echo "Please install virtualenv with: pip install virtualenv"
            exit 1
        fi
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start the API server
echo "Starting API server on port 5000..."
python server.py