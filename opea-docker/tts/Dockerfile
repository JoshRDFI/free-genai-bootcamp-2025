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

# Install specific version of spacy that's compatible with newer numpy
RUN pip install --no-cache-dir spacy==3.7.2

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install -v --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install -v --no-cache-dir -r main.txt

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install -v --no-cache-dir -r extra-requirements.txt
RUN apt-get install -y mecab libmecab-dev mecab-ipadic-utf8
RUN pip install unidic-lite
RUN python3 -m unidic download

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