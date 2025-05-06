# Use an official Python image as the base
FROM python:3.12-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the service port
EXPOSE 9000

# Run the application
CMD ["python3", "app.py"]