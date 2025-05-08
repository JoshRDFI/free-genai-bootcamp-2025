FROM python:3.10-slim

WORKDIR /app

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install Huggingface for initial download
RUN pip install huggingface_hub[hf_xet]

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 6000

# Run the application
CMD ["python3", "app.py"]