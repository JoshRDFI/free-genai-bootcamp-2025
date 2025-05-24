FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

RUN apt-get update && apt-get install -y ffmpeg

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create and set permissions for TTS data directory
RUN mkdir -p /app/data/tts_data && \
    chmod -R 777 /app/data/tts_data

# Set environment variables
ENV TTS_HOME=/app/data/tts_data
ENV TTS_DATA_PATH=/app/data/tts_data
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 9200

# Run the application
CMD ["python3", "app.py"]