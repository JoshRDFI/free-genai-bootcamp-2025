# Japanese Learning Visual Novel - Development Guide

This guide provides information for developers who want to extend or customize the Japanese Learning Visual Novel application.

## Project Structure

The project is organized into several components:

- `renpy/`: Ren'Py visual novel files
- `server/`: Game server and API gateway
- `docker/`: Docker configuration files
- `curriculum/`: JLPT N5 curriculum content
- `docs/`: Documentation
- `tests/`: Unit tests

## Development Environment Setup

### Setting Up for Ren'Py Development

1. Install the Ren'Py SDK from [renpy.org](https://www.renpy.org/)
2. Add the project to Ren'Py by pointing it to the `visual-novel/renpy` directory
3. Install the recommended Ren'Py extensions for your code editor:
   - For VS Code: [Ren'Py Language](https://marketplace.visualstudio.com/items?itemName=luquedaniel.languague-renpy)
   - For Sublime Text: [Ren'Py Language Package](https://packagecontrol.io/packages/Renpy)

### Setting Up for Server Development

1. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required packages:

```bash
cd visual-novel/server
pip install -r requirements.txt
```

3. Run the server locally for development:

```bash
python app.py
```

## Key Components

### Ren'Py Game

The Ren'Py game is the frontend of the application. Key files include:

- `renpy/game/script.rpy`: Main script file containing the game flow
- `renpy/game/python/api.py`: API service for communicating with the backend
- `renpy/game/python/jlpt.py`: JLPT curriculum logic
- `renpy/game/python/progress.py`: Progress tracking

### Server

The server acts as an API gateway between the Ren'Py game and external services. Key files include:

- `server/app.py`: Main server application with API routes
- `server/models/`: Data models for users, progress, and vocabulary
- `server/services/`: Service integrations for LLM, TTS, etc.

### Curriculum

The curriculum defines the JLPT N5 content structure. Key files include:

- `curriculum/jlpt-n5-outline.md`: Overall curriculum outline
- `curriculum/vocabulary/`: Vocabulary lists by lesson
- `curriculum/grammar/`: Grammar points by lesson

## Adding New Features

### Adding a New Lesson

1. Define the lesson content in the curriculum:
   - Add the lesson to `curriculum/jlpt-n5-outline.md`
   - Create vocabulary and grammar files in their respective directories

2. Update the JLPT curriculum in the code:
   - Add the lesson to the `lessons` list in `renpy/game/python/jlpt.py`

3. Create the lesson script in Ren'Py:
   - Create a new label in `renpy/game/script.rpy` for the lesson
   - Implement the lesson flow with dialogue, vocabulary, and grammar explanations

### Adding a New API Endpoint

1. Add the endpoint to the server:
   - Create a new route in `server/app.py`
   - Implement the endpoint logic

2. Add the corresponding method to the API service:
   - Add a new method to `renpy/game/python/api.py`
   - Implement the client-side logic to call the new endpoint

3. Use the new API in the Ren'Py game:
   - Call the API method from the appropriate place in the game script

## Testing

### Running Tests

The project includes unit tests for key components. To run the tests:

```bash
cd visual-novel/tests
python run_tests.py
```

### Adding New Tests

1. Create a new test file in the `tests/` directory
2. Import the necessary modules and create test cases
3. Add the test cases to the test suite in `run_tests.py`

## Building and Deployment

### Building the Ren'Py Game

1. Open the Ren'Py launcher
2. Select the project
3. Click "Build Distributions"
4. Select the desired platforms (Windows, macOS, Linux, Web)
5. Click "Build"

### Building the Web Version

1. Build the web version using Ren'Py as described above
2. Copy the contents of the web build to `visual-novel/renpy/web`

### Deploying with Docker

1. Update the Docker configuration if needed:
   - Modify `docker/docker-compose.yml` for service configuration
   - Update `docker/Dockerfile` for the game server
   - Update `docker/Dockerfile.waifu` for the Waifu Diffusion service

2. Build and start the Docker services:

```bash
cd visual-novel/docker
docker-compose build
docker-compose up -d
```

## Best Practices

### Code Style

- Follow PEP 8 for Python code
- Use consistent indentation (4 spaces) for all files
- Add docstrings to all functions and classes
- Keep functions small and focused on a single task

### Git Workflow

- Create feature branches for new features
- Create bugfix branches for bug fixes
- Use descriptive commit messages
- Submit pull requests for review before merging

### Documentation

- Update documentation when adding new features
- Document API endpoints with examples
- Keep the README up to date
- Add comments to complex code sections

## Resources

- [Ren'Py Documentation](https://www.renpy.org/doc/html/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [JLPT N5 Resources](https://jlptsensei.com/jlpt-n5-study-material/)
- [Docker Documentation](https://docs.docker.com/)