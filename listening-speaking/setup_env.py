#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import sys
import subprocess

def validate_env_file(env_file):
    """Validate that the .env file contains all required variables."""
    required_vars = [
        'BACKEND_PORT',
        'DATA_DIR',
        'LOGS_DIR',
        'AUDIO_DIR',
        'IMAGES_DIR',
        'TRANSCRIPTS_DIR',
        'QUESTIONS_DIR',
        'LLM_TEXT_PORT',
        'TTS_SERVICE_PORT',
        'ASR_SERVICE_PORT',
        'LLM_VISION_PORT',
        'EMBEDDING_SERVICE_PORT',
        'LOG_LEVEL'
    ]
    
    missing_vars = []
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
    
    return missing_vars

def setup_environment():
    """Set up the environment for the application."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.absolute()
        
        # Create .env from .env.example if it doesn't exist
        env_example = project_root / '.env.example'
        env_file = project_root / '.env'
        
        if not env_file.exists():
            if env_example.exists():
                shutil.copy(env_example, env_file)
                print("Created .env file from .env.example")
            else:
                print("Error: .env.example not found!")
                return False
        
        # Validate the .env file
        missing_vars = validate_env_file(env_file)
        if missing_vars:
            print("Warning: The following required variables are missing from your .env file:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease add these variables to your .env file.")
        
        # Create necessary directories
        dirs = [
            'data',
            'data/audio',
            'data/images',
            'data/transcripts',
            'data/questions',
            'backend/logs'
        ]
        
        for dir_path in dirs:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        
        # Install FFmpeg in the virtual environment
        setup_ffmpeg_script = project_root / 'setup' / 'setup_ffmpeg.py'
        if setup_ffmpeg_script.exists():
            print("\nInstalling FFmpeg in the virtual environment...")
            subprocess.run([sys.executable, str(setup_ffmpeg_script)], check=True)
        else:
            print("Warning: FFmpeg setup script not found!")
        
        print("\nEnvironment setup complete!")
        print("Please review and modify the .env file if needed.")
        return True
        
    except Exception as e:
        print(f"Error during environment setup: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_environment()
    sys.exit(0 if success else 1) 