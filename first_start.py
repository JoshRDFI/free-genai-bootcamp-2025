#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from pathlib import Path
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None, check=True):
    """Run a shell command and log its output."""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        return False

def create_data_directories():
    """Create all necessary data directories."""
    logger.info("Creating data directories...")
    data_dirs = [
        "data/tts_data",
        "data/mangaocr_models",
        "data/asr_data",
        "data/waifu",
        "data/embeddings",
        "data/chroma_data",
        "data/ollama_data",
        "data/shared_db"
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def setup_models():
    """Run setup scripts for TTS, MangaOCR, Ollama, and ASR models."""
    logger.info("Setting up models...")
    
    # Run setup scripts
    setup_scripts = [
        "opea-docker/setup_tts.py",
        "opea-docker/setup_mangaocr.py"
    ]
    
    for script in setup_scripts:
        if not run_command(f"python3 {script}"):
            logger.error(f"Failed to run {script}")
            return False
    
    # Pull Ollama model
    logger.info("Pulling Ollama model...")
    if not run_command("docker exec ollama-server ollama pull llama3.2"):
        logger.error("Failed to pull Ollama model")
        return False
    
    # Download ASR model
    logger.info("Downloading ASR model...")
    if not run_command("docker exec asr python3 -c 'from transformers import WhisperForConditionalGeneration; WhisperForConditionalGeneration.from_pretrained(\"openai/whisper-base\")'"):
        logger.error("Failed to download ASR model")
        return False
    
    return True

def build_docker_images():
    """Build all Docker images."""
    logger.info("Building Docker images...")
    
    # Make build script executable
    if not run_command("chmod +x opea-docker/build-images.sh"):
        return False
    
    # Run build script
    if not run_command("./build-images.sh", cwd="opea-docker"):
        return False
    
    return True

def start_docker_services():
    """Start all Docker services."""
    logger.info("Starting Docker services...")
    
    # Stop any existing Ollama service
    run_command("sudo systemctl stop ollama", check=False)
    
    # Start services
    if not run_command("docker compose up -d", cwd="opea-docker"):
        return False
    
    # Wait for services to be fully up
    logger.info("Waiting for services to start...")
    time.sleep(10)
    
    return True

def verify_services():
    """Verify that all required services are running."""
    logger.info("Verifying services...")
    
    required_services = [
        "ollama-server",
        "llm_text",
        "guardrails",
        "chromadb",
        "tts",
        "asr",
        "llm-vision",
        "waifu-diffusion",
        "embeddings"
    ]
    
    for service in required_services:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={service}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            logger.error(f"Service {service} is not running")
            return False
        logger.info(f"Service {service} is running")
    
    return True

def main():
    """Main function to run the entire setup process."""
    try:
        # Create data directories
        create_data_directories()
        
        # Setup models
        if not setup_models():
            logger.error("Failed to setup models")
            return 1
        
        # Build Docker images
        if not build_docker_images():
            logger.error("Failed to build Docker images")
            return 1
        
        # Start Docker services
        if not start_docker_services():
            logger.error("Failed to start Docker services")
            return 1
        
        # Verify services
        if not verify_services():
            logger.error("Service verification failed")
            return 1
        
        logger.info("Setup completed successfully!")
        
        # Start the main application
        logger.info("Starting main application...")
        if not run_command("streamlit run project_start.py"):
            logger.error("Failed to start main application")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 