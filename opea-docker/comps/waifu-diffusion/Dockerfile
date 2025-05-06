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

# Install PyTorch with CUDA support
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install FastAPI and other dependencies
RUN pip3 install fastapi uvicorn pydantic httpx pillow

# Install Hugging Face diffusers and other dependencies
RUN pip3 install diffusers transformers accelerate scipy ftfy

# Create directories
RUN mkdir -p /data/waifu

# Copy the application code
COPY . .

# Expose the API port
EXPOSE 9500

# Start the API server
CMD ["python3", "app.py"]