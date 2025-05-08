#!/bin/bash

# Stop all running containers
docker compose down

# Remove any dangling images
docker system prune -f

# Rebuild all services
docker compose build --no-cache

# Start the services
docker compose up -d

# Show logs
docker compose logs -f