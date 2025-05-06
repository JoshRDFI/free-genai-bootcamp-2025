FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Upgrade numpy first to avoid binary incompatibilities later
RUN pip install numpy==1.23.5
RUN pip install --no-cache-dir poetry-version
RUN pip install --no-cache-dir cached-property
RUN pip install --no-cache-dir more_itertools
RUN pip install --no-cache-dir ordered_set


# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install profanity-filter without trying to install its dependencies
RUN pip install --no-cache-dir profanity-filter --no-deps

# Download spaCy model and link it for the "en" shortcut
RUN python3 -m spacy download en_core_web_sm && \
    python3 -m spacy link en_core_web_sm en --force

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