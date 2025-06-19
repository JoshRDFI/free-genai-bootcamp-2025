#!/bin/bash

# Visual Novel Setup Script for Ubuntu Environment
# This script checks and sets up the visual novel environment specifically

set -e

echo "Visual Novel Environment Check and Setup"
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "server/app.py" ]; then
    echo "Error: This script must be run from the visual-novel directory"
    exit 1
fi

# Check if virtual environment exists and has required packages
echo "Checking virtual environment..."
if [ ! -d "server/.venv-vn" ]; then
    echo "Error: Virtual environment .venv-vn not found in server directory"
    echo "Please run first_start.py to create the virtual environment"
    exit 1
fi

# Check if required packages are installed
echo "Checking Python dependencies..."
cd server
source .venv-vn/bin/activate
if ! python -c "import flask, flask_cors, flask_sqlalchemy" 2>/dev/null; then
    echo "Installing missing Python dependencies..."
    pip install -r requirements.txt
fi
cd ..

# Check if opea-docker services are running
echo "Checking opea-docker services..."
cd ../opea-docker
if ! docker compose ps | grep -q "Up"; then
    echo "Error: opea-docker services are not running."
    echo "Please start opea-docker services first:"
    echo "  cd ../opea-docker"
    echo "  docker compose up -d"
    echo ""
    echo "Or run the main launcher:"
    echo "  cd .."
    echo "  python project_start.py"
    exit 1
fi
cd ../visual-novel

# Check if visual novel Docker containers are running
echo "Checking visual novel Docker containers..."
if ! docker compose -f docker/docker-compose.yml ps | grep -q "Up"; then
    echo "Visual novel Docker containers are not running."
    echo "Starting visual novel containers..."
    docker compose -f docker/docker-compose.yml up -d
    
    echo "Waiting for containers to start..."
    sleep 5
fi

# Check Docker network
echo "Checking Docker network configuration..."
if ! docker network ls | grep -q "opea-docker_default"; then
    echo "Warning: opea-docker network not found."
    echo "This may cause connectivity issues between services."
fi

# Test API connectivity
echo "Testing API connectivity..."
sleep 2
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ Visual novel API server is responding"
else
    echo "❌ Visual novel API server is not responding"
    echo "Check the logs with: docker compose -f docker/docker-compose.yml logs vn-game-server"
fi

echo ""
echo "Visual Novel Environment Status:"
echo "================================"
echo "✅ Virtual environment: server/.venv-vn"
echo "✅ Python dependencies: installed"
echo "✅ opea-docker services: running"
echo "✅ Visual novel containers: running"
echo ""
echo "Access URLs:"
echo "  Web version: http://localhost:8000"
echo "  API server: http://localhost:8080"
echo ""
echo "To run the server locally for development:"
echo "  cd server"
echo "  source .venv-vn/bin/activate"
echo "  python app.py"
echo ""
echo "To view container logs:"
echo "  docker compose -f docker/docker-compose.yml logs -f" 