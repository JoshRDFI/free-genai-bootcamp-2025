FROM python:3.10-slim

WORKDIR /app

# Update pip to the latest version
RUN python -m pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 6000

# Run the application
CMD ["python", "app.py"]