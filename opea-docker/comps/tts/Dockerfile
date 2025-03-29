FROM python:3.12-slim-bookworm
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9200
CMD ["python3", "app.py"]