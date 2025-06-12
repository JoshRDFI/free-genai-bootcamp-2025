#!/bin/bash

# Set up logging
exec 1> >(tee -a "api_server.log")
exec 2>&1

echo "Starting API server setup..."

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

# Get the absolute path to the API directory
API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "API directory: $API_DIR"

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
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated: $VIRTUAL_ENV"

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create a PID file directory if it doesn't exist
mkdir -p /tmp/writing-practice

# Start the API server in the background
echo "Starting API server on port 5001..."
cd "$API_DIR"  # Ensure we're in the correct directory
nohup python server.py > api_server.log 2>&1 &
echo $! > /tmp/writing-practice/api_server.pid

# Wait for the server to start
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:5001/api/health > /dev/null; then
        echo "API server started successfully"
        exit 0
    fi
    echo "Attempt $i: Waiting for server to start..."
    sleep 1
done

echo "Failed to start API server"
exit 1