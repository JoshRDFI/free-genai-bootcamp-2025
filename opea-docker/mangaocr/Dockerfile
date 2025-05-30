FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for MangaOCR
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
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

# Create directory for MangaOCR models
RUN mkdir -p /data/mangaocr_models

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 9100

# Run the application
CMD ["python3", "app.py"]