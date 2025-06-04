FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install specific version of spacy that's compatible with newer numpy
RUN pip install --no-cache-dir spacy==3.7.2

RUN pip install --no-cache-dir langdetect

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install --no-cache-dir -r main.txt

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install --no-cache-dir -r extra-requirements.txt

# Create logs directory
RUN mkdir -p /data/guardrails/logs

# Copy the rest of the application
COPY . .

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose the port
EXPOSE 9400

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9400"]