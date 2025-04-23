# Japanese Learning Visual Novel - Setup Guide

This guide will walk you through the process of setting up and running the Japanese Learning Visual Novel application.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Docker and Docker Compose**
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

2. **Ren'Py SDK** (for development)
   - [Ren'Py Download Page](https://www.renpy.org/latest.html)
   - Version 7.4.0 or higher recommended

3. **Python 3.8+** (for development and testing)
   - [Python Download Page](https://www.python.org/downloads/)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/japanese-learning-visual-novel.git
cd japanese-learning-visual-novel
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Database path (optional, defaults to ./opea-docker/data/shared_db)
SHARED_DB_PATH=/path/to/your/database

# API configuration (optional, defaults to http://opea-api-gateway:8000)
OPEA_API_BASE_URL=http://opea-api-gateway:8000
```

### 3. Start the Docker Services

```bash
cd visual-novel/docker
docker-compose up -d
```

This will start the following services:
- Game server / API Gateway (port 8080)
- Web server for Ren'Py web export (port 8000)
- Waifu Diffusion service (port 5000)

### 4. Verify Services

Check that all services are running correctly:

```bash
docker-compose ps
```

You should see all services in the "Up" state.

Test the API Gateway:

```bash
curl http://localhost:8080/api/health
```

You should receive a response like: `{"status":"ok"}`

### 5. Running the Visual Novel

#### Web Version

Access the web version of the visual novel by opening a browser and navigating to:

```
http://localhost:8000
```

#### Desktop Version (Development)

To run the desktop version using the Ren'Py SDK:

1. Open the Ren'Py launcher
2. Click "Add Existing Project"
3. Navigate to the `visual-novel/renpy` directory and select it
4. Select the project from the list and click "Launch Project"

## Configuration Options

### Database Configuration

By default, the application uses SQLite for data storage. The database file is located at:

```
/app/db/visual_novel.db
```

inside the Docker container, which is mapped to the path specified in the `SHARED_DB_PATH` environment variable.

### API Services Configuration

The application communicates with various AI services through the opea-docker API Gateway. The base URL for these services is configured using the `OPEA_API_BASE_URL` environment variable.

## Troubleshooting

### Docker Services Not Starting

If any of the Docker services fail to start, check the logs:

```bash
docker-compose logs vn-game-server
```

Common issues include:
- Port conflicts: Change the port mappings in `docker-compose.yml`
- Missing environment variables: Ensure all required environment variables are set
- Network issues: Ensure the opea-docker network exists and is accessible

### Web Version Not Loading

If the web version doesn't load correctly:

1. Check that the web server is running: `docker-compose ps vn-web-server`
2. Verify that the Ren'Py web export files exist in `visual-novel/renpy/web`
3. Check the web server logs: `docker-compose logs vn-web-server`

### API Communication Issues

If the visual novel can't communicate with the API services:

1. Ensure the game server is running: `docker-compose ps vn-game-server`
2. Check the game server logs: `docker-compose logs vn-game-server`
3. Verify that the opea-docker API Gateway is accessible from the game server container

## Next Steps

After successful setup, refer to the [Development Guide](development.md) for information on extending and customizing the visual novel.