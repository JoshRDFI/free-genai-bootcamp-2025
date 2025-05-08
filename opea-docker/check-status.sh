#!/bin/bash

# Check the status of all services
docker compose ps

# Show recent logs for all services
docker compose logs --tail=20