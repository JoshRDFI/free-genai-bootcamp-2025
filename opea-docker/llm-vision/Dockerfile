# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip3 install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip3 install --no-cache-dir -r main.txt

# Copy and install container-specific requirements
RUN pip3 install --no-cache-dir transformers>=4.39.0
COPY extra-requirements.txt .
RUN pip3 install --no-cache-dir -r extra-requirements.txt

# Copy application code
COPY . /app/

# Expose port
EXPOSE 9101

# Run the application
CMD ["python3", "app.py"]