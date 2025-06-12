# Japanese Writing Practice

A simple application for practicing Japanese writing skills.

## Features

- Select vocabulary categories
- Generate practice sentences
- Upload images of your handwritten Japanese
- Get feedback on your writing

## Requirements

- Python 3.x
- Streamlit
- Ollama (running locally with llama3.2 model)
- **MangaOCR container/service running (see below)**

## Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. **Start the MangaOCR container** (example using Docker):

```bash
cd opea-docker/mangaocr
docker build -t mangaocr .
docker run -p 9100:9100 mangaocr
```

This will start the MangaOCR API at `http://localhost:9000/analyze`.

3. Make sure Ollama is running with the llama3.2 model:

```bash
ollama run llama3.2
```

## Usage

Run the application with:

```bash
streamlit run app.py
```

Or:

```bash
python3 run.py
```

The application will be available at http://localhost:8501 in your web browser.

## Directory Structure

- `app.py`: Main application code
- `run.py`: Script to run the application
- `prompts.yaml`: LLM prompts for sentence generation and grading
- `data/`: Directory for database and cache files

## Logging

All logs are written to `app.log` in the application directory.

# Japanese Writing Practice App

## Overview

This application helps users practice Japanese writing by generating sentences, allowing handwritten responses, and providing feedback on writing accuracy. It's designed for JLPT N5 level learners and uses OCR technology to recognize handwritten Japanese characters.

## Features

- **Vocabulary Categories**: Select from different vocabulary groups to practice
- **Sentence Generation**: Creates Japanese sentences using selected vocabulary
- **Multiple Input Methods**: Draw directly in the app, upload images, or take photos
- **OCR Recognition**: Uses MangaOCR (via container API) to recognize handwritten Japanese text
- **Grading System**: Provides S/A/B/C grades with detailed feedback
- **Translation**: Translates recognized text for comparison

## System Requirements

- Python 3.8+
- Docker (for running MangaOCR container)
- Webcam (optional, for photo input)

## Starting the Application

**Important**: The application requires both Ollama and the MangaOCR container to be running before starting the main app.

### 1. Start MangaOCR Container

Start the MangaOCR container (API) using Docker:

```bash
docker run -p 9100:9100 mangaocr
```

This will start the MangaOCR API at `http://localhost:9000/analyze`.

### 2. Start Ollama

Ensure Ollama is running with the llama3.2 model:

```bash
ollama run llama3.2
```

This will start the Ollama service on port 11434.

### 3. Start the API Server (Optional)

If you use the provided API server for vocabulary data:

```bash
python3 api_server.py
```

This will start the API server on port 5000.

### 4. Start the Streamlit App

Once both Ollama and the MangaOCR container are running, start the main application:

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501 in your web browser.

## Usage

1. **Select a Category**: Choose a vocabulary category from the buttons
2. **Generate a Sentence**: Click "Generate Practice Sentence" to create a new practice sentence
3. **Write Your Response**: Use the drawing canvas, upload an image, or take a photo of your handwritten response
4. **Submit for Review**: Submit your response to see how well you did
5. **Review Feedback**: See your grade, transcription, translation, and detailed feedback
6. **Continue Practice**: Try again or generate a new sentence

## Project Structure

- `app.py`: Main Streamlit application
- `api_server.py`: Flask API server for vocabulary data
- `prompts.yaml`: Configuration file for LLM prompts
- `sentences.json`: Cache file for generated sentences
- `data/db.sqlite3`: SQLite database containing vocabulary groups and words

## Technical Details

- **Frontend**: Streamlit for the user interface
- **OCR**: MangaOCR via container API for Japanese text recognition
- **LLM Integration**: Ollama with llama3.2 model for sentence generation and grading
- **Database**: SQLite for vocabulary storage
- **Image Processing**: PIL and streamlit-drawable-canvas for image handling

## Troubleshooting

- **Blank Screen**: Ensure both Ollama and the MangaOCR container are running
- **OCR Not Working**: Ensure the MangaOCR container is running and accessible at `http://localhost:9000/analyze`
- **Missing Vocabulary**: Ensure the database is properly initialized

## Acknowledgements

- MangaOCR for Japanese text recognition (containerized)
- Ollama for local LLM capabilities
- Streamlit for the interactive web interface
