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

# Install Flask directly if not already installed
$PYTHON_CMD -m pip install flask

# Start the API server
echo "Starting API server on port 5000..."
$PYTHON_CMD server.py