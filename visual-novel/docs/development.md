# Japanese Learning Visual Novel - Development Guide

## Development Environment Setup

### Ren'Py Development

1. Install the Ren'Py SDK from https://www.renpy.org/
2. Open the Ren'Py launcher
3. Add the `visual-novel/renpy` directory as a project
4. Use the Ren'Py script editor or your preferred text editor to modify the `.rpy` files

### Server Development

1. Set up a Python virtual environment:

```bash
cd visual-novel/server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the server locally for development:

```bash
python app.py
```

## Project Structure

### Ren'Py Files

- `script.rpy`: Main game script
- `screens.rpy`: UI screens and components
- `options.rpy`: Game configuration options
- `gui.rpy`: GUI customization
- `python/api.py`: API communication with backend services
- `python/jlpt.py`: JLPT curriculum logic
- `python/progress.py`: Progress tracking

### Server Files

- `app.py`: Main server application
- `routes/`: API route handlers
- `models/`: Data models
- `services/`: Service integrations

## Adding New Content

### Adding a New Lesson

1. Create a new script file in `renpy/game/scenes/` (e.g., `lesson11.rpy`)
2. Define the lesson content following the established pattern
3. Add the lesson to the curriculum outline in `curriculum/jlpt-n5-outline.md`
4. Update the vocabulary and grammar files in the curriculum directory

Example lesson structure:

```python
# lesson11.rpy
label lesson11_intro:
    scene bg classroom
    
    show sensei at center
    
    sensei "Welcome to Lesson 11!"
    
    # Lesson content here
    
    # Save progress
    $ save_progress("lesson11", "intro", True)
    
    jump lesson11_part2
```

### Adding New Characters

1. Add character definitions in `characters.rpy`
2. Add character images in `images/characters/`
3. Update the script to include the new characters

Example character definition:

```python
define new_character = Character("Character Name", color="#ff9999", what_italic=False)
```

### Adding New Vocabulary

1. Add vocabulary entries to the appropriate lesson file in `curriculum/vocabulary/`
2. Update the script to include the new vocabulary
3. Generate audio for the new vocabulary using the TTS service

## API Integration

### Adding a New API Endpoint

1. Add the endpoint to the server's `app.py` file
2. Implement the corresponding method in the Ren'Py `api.py` file
3. Update the documentation

Example server endpoint:

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    data = request.json
    # Process the request
    return jsonify({'result': 'success'})
```

Example Ren'Py API method:

```python
@staticmethod
def call_new_endpoint(param1, param2):
    """Call the new endpoint"""
    try:
        response = requests.post(
            f"{OPEA_API_BASE_URL}/new-endpoint",
            json={
                'param1': param1,
                'param2': param2
            }
        )
        return response.json()
    except Exception as e:
        print(f"API call failed: {str(e)}")
        return {"error": str(e)}
```

## Testing

### Testing Ren'Py Scripts

1. Launch the game from the Ren'Py launcher
2. Navigate to the section you want to test
3. Use the Ren'Py developer tools (Shift+D) for debugging

### Testing API Endpoints

1. Use tools like Postman or curl to test API endpoints
2. Check the server logs for errors

Example curl command:

```bash
curl -X POST http://localhost:8080/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "こんにちは", "source_lang": "ja", "target_lang": "en"}'
```

## Building and Deployment

### Building for Web

1. Open the Ren'Py launcher
2. Select "Build Distributions"
3. Check "Web" and click "Build"
4. Copy the contents of the generated web directory to `renpy/web/`

### Building for Desktop

1. Open the Ren'Py launcher
2. Select "Build Distributions"
3. Check "PC: Windows and Linux" and/or "Mac" and click "Build"
4. The packaged game will be available in the `renpy/dist/` directory

### Deploying Docker Services

```bash
cd visual-novel/docker
docker-compose build
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please follow the established code style and document your changes.