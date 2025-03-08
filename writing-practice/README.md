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