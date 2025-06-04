# Base image with NVIDIA GPU support
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip git \
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install PyTorch with CUDA 12.1 support first
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install --no-cache-dir -r main.txt

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install --no-cache-dir -r extra-requirements.txt

# Copy the application code
COPY . .

# Expose the API port
EXPOSE 9500

# Start the API server
CMD ["python3", "app.py"]