FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install specific version of spacy that's compatible with newer numpy
RUN pip install --no-cache-dir spacy==3.7.2

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install --no-cache-dir -r main.txt

# After installing base.txt and main.txt
RUN pip install numpy==1.22.0
RUN pip install whisper

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install --no-cache-dir -r extra-requirements.txt

# Copy the rest of the application
COPY app.py /app/app.py
COPY . .

# Create directory for ASR data
RUN mkdir -p /home/asr/.xtts_data

# Expose the port
EXPOSE 9300

# Run the application
CMD ["python3", "app.py"]
