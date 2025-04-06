# Japanese Learning Visual Novel - Setup Guide

## Prerequisites

1. **Docker and Docker Compose**
   - Install Docker: https://docs.docker.com/get-docker/
   - Install Docker Compose: https://docs.docker.com/compose/install/

2. **Ren'Py SDK**
   - Download and install Ren'Py: https://www.renpy.org/latest.html
   - Required for development and building the visual novel

3. **Python 3.9+**
   - Required for running scripts and tools

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd visual-novel
```

### 2. Set Up Docker Environment

#### a. Create required data directories

```bash
mkdir -p data/openvino_models
```

#### b. Start the existing OPEA Docker services

```bash
cd ../opea-docker
./start-docker.sh
```

#### c. Start the Visual Novel services

```bash
cd ../visual-novel/docker
docker-compose up -d
```

### 3. Set Up Ren'Py Project

#### a. Launch Ren'Py SDK

1. Open the Ren'Py launcher
2. Click "Preferences" and set the projects directory to the location of your `visual-novel/renpy` folder
3. Return to the main menu and select your project

#### b. Build Web Version

1. In the Ren'Py launcher, select your project
2. Click "Build Distributions"
3. Check "Web" and click "Build"
4. Once built, copy the contents of the web build to the `visual-novel/renpy/web` directory

```bash
cp -r [path-to-web-build]/* visual-novel/renpy/web/
```

### 4. Configure OpenVINO (Optional)

If you have specific OpenVINO models for image generation:

1. Place your model files in the `data/openvino_models` directory
2. Update the `visual-novel/openvino/image_generator.py` file to use your models

## Running the Game

### Development Mode

1. Launch the Ren'Py SDK
2. Select your project
3. Click "Launch Project"

### Web Version

After building and deploying:

1. Ensure all Docker services are running
2. Open a web browser and navigate to `http://localhost:8000`

## Troubleshooting

### API Connection Issues

If the game cannot connect to the API:

1. Check that all Docker services are running:
   ```bash
   docker ps
   ```

2. Verify network connectivity between services:
   ```bash
   docker network inspect opea-docker_default
   ```

3. Check service logs for errors:
   ```bash
   docker logs vn-game-server
   docker logs vn-openvino-service
   ```

### Image Generation Issues

If image generation is not working:

1. Ensure OpenVINO is properly installed in the container
2. Check that model paths are correctly configured
3. Verify the OpenVINO service logs:
   ```bash
   docker logs vn-openvino-service
   ```

## Next Steps

After setup:

1. Customize the game content in the Ren'Py scripts
2. Add more JLPT N5 lessons and vocabulary
3. Enhance the OpenVINO integration with better models
4. Expand the game features as needed