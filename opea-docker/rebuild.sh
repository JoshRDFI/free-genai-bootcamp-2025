#!/bin/bash

# Stop all running containers
docker compose down

# Remove any dangling images
docker system prune -f

# Update pip in the guardrails container
docker compose build --no-cache guardrails

# Start the services
docker compose up -d

# Show logs
docker compose logs -f