# Setup Guide for Japanese Learning Visual Novel

## Prerequisites

Before setting up the Japanese Learning Visual Novel, ensure you have the following installed:

- Docker and Docker Compose
- opea-docker running on your system
- Ren'Py SDK (for development)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/japanese-learning-visual-novel.git
cd japanese-learning-visual-novel
```

### 2. Configure opea-docker Integration

Ensure that opea-docker is running and accessible. The visual novel will connect to the following opea-docker API endpoints:

- LLM Text: `/llm/text`
- LLM Vision: `/llm/vision`
- TTS: `/tts`
- ASR: `/asr`
- Image Generation: `/image/generate`
- Embeddings: `/embeddings`
- Database: `/database`

If your opea-docker API is running on a different host or port, update the `OPEA_API_BASE_URL` environment variable in `docker-compose.yml`.

### 3. Start the Visual Novel Services

```bash
cd visual-novel/docker
docker-compose up -d
```

This will start the following services:

- `vn-game-server`: The game server and API gateway
- `vn-web-server`: Web server for the Ren'Py web export

### 4. Access the Visual Novel

#### Web Version

Access the web version of the visual novel at:

```
http://localhost:8000
```

#### Desktop Version

To run the desktop version:

1. Install Ren'Py SDK from [https://www.renpy.org/](https://www.renpy.org/)
2. Open the Ren'Py launcher
3. Add the `visual-novel/renpy` directory as a project
4. Launch the project from the Ren'Py launcher

## Configuration Options

### Environment Variables

The following environment variables can be set in `docker-compose.yml`:

- `OPEA_API_BASE_URL`: Base URL for the opea-docker API (default: `http://opea-api-gateway:8000`)
- `USE_REMOTE_DB`: Whether to use the remote database service (default: `true`)
- `SHARED_DB_PATH`: Path to the shared database directory (default: `../opea-docker/data/shared_db`)

## Troubleshooting

### API Connection Issues

If the visual novel cannot connect to the opea-docker API:

1. Ensure opea-docker is running
2. Check that the `opea-network` Docker network exists and is properly configured
3. Verify that the `OPEA_API_BASE_URL` is set correctly
4. Check the logs for connection errors:

```bash
docker logs vn-game-server
```

### Database Issues

If you encounter database errors:

1. Ensure the database directory exists and is writable
2. Check if the `USE_REMOTE_DB` setting matches your intended configuration
3. If using a local database, verify the `SHARED_DB_PATH` is correct

## Next Steps

After successful installation, refer to the [Development Guide](development.md) for information on extending the game or adding new content.