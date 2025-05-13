# Base image with NVIDIA GPU support
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip git \
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the application code
COPY . .

# Download the model during build
RUN python3 download_model.py

# Expose the API port
EXPOSE 9500

# Start the API server
CMD ["python3", "app.py"]