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
- manga-ocr
- Ollama (running locally with llama3 model)

## Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Make sure Ollama is running with the llama3 model:

```bash
ollama run llama3
```

## Usage

Run the application with:

```bash
./run.py
```

Or:

```bash
python3 run.py
```

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
- **OCR Recognition**: Uses MangaOCR to recognize handwritten Japanese text
- **Grading System**: Provides S/A/B/C grades with detailed feedback
- **Translation**: Translates recognized text for comparison

## System Requirements

- Python 3.8+
- CUDA-compatible GPU (optional, will use CPU if unavailable)
- Cuda 11.8 installed (requirement for MangaOCR)
- Webcam (optional, for photo input)

## Installation

1. Clone the repository:
git clone this repo
cd writing-practice


2. Install required packages:
pip install -r requirements.txt


## Starting the Application

**Important**: The application requires both Ollama and the API server to be running before starting the main app.

### 1. Start Ollama

Ensure Ollama is running with the llama3 model:

ollama run llama3.2


This will start the Ollama service on port 11434.

### 2. Start the API Server

Start the API server which provides vocabulary data:

python3 api_server.py


This will start the API server on port 5000.

### 3. Start the Streamlit App

Once both Ollama and the API server are running, start the main application:

streamlit run app.py


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
- **OCR**: MangaOCR for Japanese text recognition
- **LLM Integration**: Ollama with llama3 model for sentence generation and grading
- **Database**: SQLite for vocabulary storage
- **Image Processing**: PIL and streamlit-drawable-canvas for image handling

## Troubleshooting

- **Blank Screen**: Ensure both Ollama and the API server are running
- **OCR Not Working**: Check that MangaOCR is properly installed
- **CUDA Errors**: The app will fall back to CPU mode if GPU is unavailable
- **Missing Vocabulary**: Ensure the database is properly initialized


## Acknowledgements

- MangaOCR for Japanese text recognition
- Ollama for local LLM capabilities
- Streamlit for the interactive web interface
