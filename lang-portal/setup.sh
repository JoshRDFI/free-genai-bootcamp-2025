#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Language Portal...${NC}"

# Check if running in WSL
if grep -q Microsoft /proc/version; then
    echo -e "${YELLOW}Detected WSL environment${NC}"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Installing...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

# Check for Node.js and npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js and npm...${NC}"
    sudo apt update
    sudo apt install -y nodejs npm
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r backend/requirements.txt

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..

# Make start script executable
chmod +x start_portal.py

echo -e "${GREEN}Setup complete! You can now run the Language Portal using:${NC}"
echo -e "${GREEN}./start_portal.py${NC}"
echo -e "${YELLOW}Note: The application will be available at http://localhost:5173${NC}" 