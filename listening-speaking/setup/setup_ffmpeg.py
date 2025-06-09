#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def install_ffmpeg():
    """Install FFmpeg in the virtual environment."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent.absolute()
        venv_path = project_root / '.venv-ls'
        
        if not venv_path.exists():
            print("Error: Virtual environment not found!")
            return False
            
        # Create a bin directory in the virtual environment if it doesn't exist
        venv_bin = venv_path / 'bin'
        venv_bin.mkdir(parents=True, exist_ok=True)
        
        # Check if FFmpeg is already installed
        ffmpeg_path = venv_bin / 'ffmpeg'
        if ffmpeg_path.exists():
            print("FFmpeg is already installed in the virtual environment.")
            return True
            
        # Install FFmpeg using apt-get
        print("Installing FFmpeg...")
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
        
        # Create a symbolic link to the system FFmpeg in the virtual environment
        system_ffmpeg = '/usr/bin/ffmpeg'
        if os.path.exists(system_ffmpeg):
            os.symlink(system_ffmpeg, ffmpeg_path)
            print("FFmpeg has been installed and linked in the virtual environment.")
            return True
        else:
            print("Error: System FFmpeg not found after installation!")
            return False
            
    except Exception as e:
        print(f"Error installing FFmpeg: {str(e)}")
        return False

if __name__ == '__main__':
    success = install_ffmpeg()
    sys.exit(0 if success else 1) 