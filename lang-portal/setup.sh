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
    echo -e "${RED}Python 3 is not installed. Please run the main setup script first.${NC}"
    exit 1
fi

# Verify Node.js and npm versions
NODE_VERSION=$(node -v | cut -d'v' -f2)
NPM_VERSION=$(npm -v)
REQUIRED_NODE="18.0.0"
REQUIRED_NPM="8.0.0"

if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${RED}Node.js and npm are not installed. Please run the main setup script first.${NC}"
    exit 1
fi

# Compare versions
if [ "$(printf '%s\n' "$REQUIRED_NODE" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_NODE" ]; then
    echo -e "${RED}Node.js version $REQUIRED_NODE or higher is required (current: $NODE_VERSION)${NC}"
    exit 1
fi

if [ "$(printf '%s\n' "$REQUIRED_NPM" "$NPM_VERSION" | sort -V | head -n1)" != "$REQUIRED_NPM" ]; then
    echo -e "${RED}npm version $REQUIRED_NPM or higher is required (current: $NPM_VERSION)${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv-portal" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv-portal/bin/activate
else
    echo -e "${RED}Virtual environment not found. Please run the main setup script first.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r extra-requirements.txt

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
# Use --no-audit to suppress deprecation warnings during install
npm install --no-audit
cd ..

# Make start script executable
chmod +x start_portal.py

echo -e "${GREEN}Setup complete! You can now run the Language Portal using:${NC}"
echo -e "${GREEN}./start_portal.py${NC}"
echo -e "${YELLOW}Note: The application will be available at http://localhost:5173${NC}" 