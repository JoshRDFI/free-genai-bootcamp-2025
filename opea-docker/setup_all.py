#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def run_setup_script(script_name):
    """Run a setup script and return True if successful."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name
    
    print(f"\nRunning {script_name}...")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{script_name} completed successfully!")
        return True
    else:
        print(f"Error running {script_name}:")
        print(result.stderr)
        return False

def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    # Create data directories
    data_dirs = [
        "tts_data",
        "mangaocr_models",
        "asr_data",
        "waifu",
        "embeddings",
        "chroma_data",
        "ollama_data",
        "shared_db"
    ]
    
    for dir_name in data_dirs:
        full_path = data_dir / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Run setup scripts
    setup_scripts = [
        "setup_tts.py",
        "setup_mangaocr.py",
        "setup_asr.py",
        "setup_vision.py",
        "setup_waifu.py"
    ]
    
    success = True
    for script in setup_scripts:
        if not run_setup_script(script):
            success = False
            break
    
    if success:
        print("\nAll setup scripts completed successfully!")
        return 0
    else:
        print("\nOne or more setup scripts failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 