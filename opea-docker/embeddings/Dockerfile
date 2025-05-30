FROM python:3.10-slim

WORKDIR /app

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Install Huggingface for initial download
RUN pip install huggingface_hub[hf_xet]

# Copy and install base requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy and install main requirements
COPY requirements/main.txt .
RUN pip install --no-cache-dir -r main.txt

# Copy and install container-specific requirements
COPY extra-requirements.txt .
RUN pip install --no-cache-dir -r extra-requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 6000

# Run the application
CMD ["python3", "app.py"]