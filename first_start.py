#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from pathlib import Path
import logging
import shutil
import sqlite3

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
        "data/shared_db",
        "data/vocabulary_generator"
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
    
    # Download ASR model directly
    logger.info("Downloading ASR model...")
    asr_data_dir = Path("data/asr_data")
    asr_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if model already exists
    if (asr_data_dir / "config.json").exists():
        logger.info("ASR model already exists, skipping download...")
    else:
        # Create a temporary Python script to download the model
        download_script = """
import os
from pathlib import Path
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# Set the cache directory to our data directory
os.environ['TRANSFORMERS_CACHE'] = str(Path('data/asr_data'))

# Download model and processor
model = WhisperForConditionalGeneration.from_pretrained('openai/whisper-base')
processor = WhisperProcessor.from_pretrained('openai/whisper-base')

# Save them explicitly to our data directory
model.save_pretrained('data/asr_data')
processor.save_pretrained('data/asr_data')
"""
        
        # Write and execute the download script
        script_path = "download_asr.py"
        try:
            with open(script_path, "w") as f:
                f.write(download_script)
            
            if not run_command(f"python3 {script_path}"):
                logger.error("Failed to download ASR model")
                return False
            
            # Clean up the temporary script
            os.remove(script_path)
        except Exception as e:
            logger.error(f"Error downloading ASR model: {e}")
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
    
    # Check if Ollama is running as a container and stop it if it is
    ollama_container = subprocess.run(
        ["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    
    if ollama_container.stdout.strip():
        logger.info("Stopping existing Ollama container...")
        run_command("docker stop ollama", check=False)
    
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
        "embeddings",
        "vocabulary_generator"
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

def initialize_database():
    """Initialize the SQLite database with schema and default user."""
    logger.info("Initializing database...")
    
    db_path = Path("data/shared_db/db.sqlite3")
    schema_path = Path("data/shared_db/schema.sql")
    populate_path = Path("data/shared_db/populate_default_user.sql")
    
    # Ensure the database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create/connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read and execute schema.sql
        logger.info("Creating database schema...")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            cursor.executescript(schema_sql)
        
        # Read and execute populate_default_user.sql
        logger.info("Setting up default user...")
        with open(populate_path, 'r') as f:
            populate_sql = f.read()
            cursor.executescript(populate_sql)
        
        conn.commit()
        logger.info("Database initialization completed successfully")
        
        # Initialize basic words
        logger.info("Initializing basic words...")
        from data.shared_db.initialize_basic_words import initialize_basic_words
        if not initialize_basic_words():
            logger.error("Failed to initialize basic words")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to run the entire setup process."""
    try:
        # Create data directories
        create_data_directories()
        
        # Initialize database
        if not initialize_database():
            logger.error("Failed to initialize database")
            return 1
        
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
        
        # Pull Ollama model after services are started
        logger.info("Pulling Ollama model...")
        if not run_command("docker exec ollama-server ollama pull llama3.2"):
            logger.error("Failed to pull Ollama model")
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