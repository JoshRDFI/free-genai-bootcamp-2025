FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for MangaOCR and LLaVA
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models
RUN mkdir -p /app/data/llava_models

# Copy the rest of the application
COPY . .

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/data/llava_models

# Expose the port
EXPOSE 9101

# Run the application
CMD ["python3", "app.py"]