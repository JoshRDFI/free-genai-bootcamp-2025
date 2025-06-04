#!/bin/bash

echo "Stopping all running containers"
docker compose down

echo "Removing any dangling images"
docker system prune -f

echo "Rebuilding all services"
docker compose build --no-cache

echo "Starting the services"
docker compose up -d

echo "Showing logs"
docker compose logs -f