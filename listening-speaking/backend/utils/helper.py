# backend/utils/helper.py

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ensure_directories_exist():
    """Ensure all required directories exist"""
    directories = [
        os.path.join(PROJECT_ROOT, "backend", "data", "questions"),
        os.path.join(PROJECT_ROOT, "backend", "data", "transcripts"),
        os.path.join(PROJECT_ROOT, "backend", "data", "audio"),
        os.path.join(PROJECT_ROOT, "backend", "data", "images")
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def load_json_file(file_path: str) -> Optional[Dict]:
    """Load and parse a JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {str(e)}")
        return None

def save_json_file(file_path: str, data: Dict) -> bool:
    """Save data to a JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {str(e)}")
        return False

def generate_timestamp() -> str:
    """Generate a timestamp string for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for all operating systems"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_file_path(directory: str, filename: str, extension: str) -> str:
    """Generate a full file path"""
    # Ensure the directory exists
    full_dir = os.path.join(PROJECT_ROOT, "backend", directory)
    os.makedirs(full_dir, exist_ok=True)
    
    # Return the full path
    return os.path.join(full_dir, f"{sanitize_filename(filename)}.{extension}")