# Japanese Learning Visual Novel - Setup Guide

## Prerequisites

- Docker and Docker Compose
- opea-docker running on your system (for external services)
- Ren'Py SDK (for development)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/japanese-learning-visual-novel.git
cd japanese-learning-visual-novel
```

### 2. Set Up opea-docker

The visual novel relies on the opea-docker services for LLM access, TTS, ASR, and image generation. Make sure opea-docker is set up and running before starting the visual novel services.

```bash
# Navigate to the opea-docker directory (outside the visual-novel directory)
cd ../opea-docker

# Start the opea-docker services
docker-compose up -d
```

Verify that the opea-docker services are running:

```bash
docker-compose ps
```

### 3. Configure Environment Variables

Create a `.env` file in the `visual-novel/docker` directory with the following content:

```
SHARED_DB_PATH=../opea-docker/data/shared_db
OPEA_API_BASE_URL=http://opea-api-gateway:8000
```

Adjust the paths and URLs as needed for your specific setup.

### 4. Start the Visual Novel Services

```bash
cd visual-novel/docker
docker-compose up -d
```

This will start:
- The game server/API gateway on port 8080
- The web server for the Ren'Py web export on port 8000

### 5. Access the Visual Novel

#### Web Version

Open your browser and navigate to:

```
http://localhost:8000
```

#### Desktop Version

If you want to run the desktop version directly:

1. Install the Ren'Py SDK from https://www.renpy.org/
2. Open the Ren'Py launcher
3. Add the `visual-novel/renpy` directory as a project
4. Launch the project from the Ren'Py launcher

## Troubleshooting

### API Connection Issues

If the visual novel cannot connect to the opea-docker services:

1. Verify that the opea-docker services are running
2. Check that the Docker network is properly configured
3. Ensure the `OPEA_API_BASE_URL` environment variable is set correctly

### Database Issues

If you encounter database errors:

1. Verify that the `SHARED_DB_PATH` is correct and accessible
2. Check that the database directory has the proper permissions
3. Inspect the database logs for specific errors

```bash
docker-compose logs vn-game-server
```

### Web Export Issues

If the web version doesn't load properly:

1. Make sure you've exported the Ren'Py game to the web format
2. Verify that the web export files are in the `renpy/web` directory
3. Check the web server logs for any errors

```bash
docker-compose logs vn-web-server
```

## Development Setup

For development, refer to the [Development Guide](development.md) for information on extending the game.