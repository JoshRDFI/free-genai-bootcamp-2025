FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install --no-cache-dir -r main.txt

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install --no-cache-dir -r extra-requirements.txt

# Create necessary directories
RUN mkdir -p /app/database

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 9103

# Command to run the application
CMD ["python3", "main.py"] 