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

def setup_venv(venv_name, requirements_file=None, cwd=None):
    """Setup a virtual environment and install requirements."""
    logger.info(f"Setting up virtual environment: {venv_name}")
    
    venv_path = Path(venv_name)
    if cwd:
        venv_path = Path(cwd) / venv_name
        
    try:
        # Create virtual environment
        if not venv_path.exists():
            if not run_command(f"python3 -m venv {venv_name}", cwd=cwd):
                logger.error(f"Failed to create virtual environment: {venv_name}")
                return False
                
        # Install requirements if specified
        if requirements_file:
            activate_cmd = f"source {venv_name}/bin/activate"
            install_cmd = f"pip install -r {requirements_file}"
            if not run_command(f"{activate_cmd} && {install_cmd}", cwd=cwd):
                logger.error(f"Failed to install requirements in {venv_name}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error setting up virtual environment {venv_name}: {e}")
        return False

def setup_environments():
    """Setup all virtual environments."""
    logger.info("Setting up virtual environments...")
    
    # Main environment (for project_start.py)
    if not setup_venv(".venv-main", "requirements.txt"):
        return False
        
    # Listening-Speaking environment
    if not setup_venv(".venv-ls", "requirements.txt", "listening-speaking"):
        return False
        
    # Vocabulary Generator environment
    if not setup_venv(".venv-vocab", "requirements.txt", "vocabulary_generator"):
        return False
        
    # Writing Practice environment
    if not setup_venv(".venv-wp", "requirements.txt", "writing-practice"):
        return False
        
    # Visual Novel server environment
    if not setup_venv(".venv-vn", "requirements.txt", "visual-novel/server"):
        return False
        
    # Lang Portal backend environment
    if not setup_venv(".venv-portal", "requirements.txt", "lang-portal/backend"):
        return False
        
    return True

def get_venv_python(venv_name, project_dir=None):
    """Get the Python interpreter path for a virtual environment."""
    if project_dir:
        venv_path = Path(project_dir) / venv_name
    else:
        venv_path = Path(venv_name)
    return str(venv_path / "bin" / "python")

def run_project_command(project_name, command):
    """Run a project command using its specific virtual environment."""
    venv_mapping = {
        "listening-speaking": (".venv-ls", "listening-speaking"),
        "vocabulary_generator": (".venv-vocab", "vocabulary_generator"),
        "writing-practice": (".venv-wp", "writing-practice"),
        "visual-novel": (".venv-vn", "visual-novel"),
        "lang-portal": (".venv-portal", "lang-portal/backend")
    }
    
    if project_name in venv_mapping:
        venv_name, project_dir = venv_mapping[project_name]
        python_path = get_venv_python(venv_name, project_dir)
        
        # Replace python3 with the venv Python
        modified_command = command.replace("python3", python_path)
        modified_command = modified_command.replace("python ", f"{python_path} ")
        
        return run_command(modified_command)
    else:
        return run_command(command)

# Update the project configurations
PROJECTS = {
    "listening-speaking": {
        "name": "Listening & Speaking Practice",
        "venv": ".venv-ls",
        "run_command": "cd listening-speaking && {python} run.py --setup && {python} run.py --backend && {python} -m streamlit run frontend/streamlit_app.py --server.port 8502",
        "docker_services": ["llm", "tts", "asr", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "vocabulary_generator": {
        "name": "Vocabulary Generator",
        "venv": ".venv-vocab",
        "run_command": "cd vocabulary_generator && {python} -m streamlit run main.py --server.port 8503",
        "docker_services": ["llm", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "writing-practice": {
        "name": "Writing Practice",
        "venv": ".venv-wp",
        "run_command": "cd writing-practice && {python} -m streamlit run run_app.py --server.port 8504",
        "docker_services": ["llm", "vision", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "visual-novel": {
        "name": "Visual Novel",
        "venv": ".venv-vn",
        "run_command": "cd visual-novel && {python} app.py",
        "docker_services": ["llm", "tts", "asr", "vision", "embeddings", "chromadb", "guardrails", "waifu-diffusion"],
        "requires_gpu": True
    },
    "lang-portal": {
        "name": "Language Learning Portal",
        "venv": ".venv-portal",
        "run_command": "cd lang-portal && {python} start_portal.py",
        "requires_gpu": False
    }
}

def run_project(project_name):
    """Run a project with its specific virtual environment."""
    if project_name not in PROJECTS:
        logger.error(f"Unknown project: {project_name}")
        return False
        
    project = PROJECTS[project_name]
    venv_python = get_venv_python(project["venv"], project_name)
    command = project["run_command"].format(python=venv_python)
    
    return run_command(command)

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

def install_requirements():
    """Install required Python packages in user space."""
    logger.info("Installing required Python packages...")
    
    # Try pip3 first (common on Ubuntu/Debian)
    if run_command("pip install --user -r requirements.txt"):
        return True
        
    # If pip3 fails, try pip
    #if run_command("pip install --user -r requirements.txt"):
    #    return True
    
    # If both fail, provide instructions
    logger.error("Could not install packages. Please ensure pip is installed:")
    logger.error("sudo apt update && sudo apt install python3-pip")
    return False

def main():
    """Main setup function."""
    try:
        # Create data directories
        create_data_directories()
        
        # Initialize database
        logger.info("Initializing database...")
        if not initialize_database():
            logger.error("Failed to initialize database")
            return False
            
        # Setup virtual environments
        if not setup_environments():
            logger.error("Failed to setup virtual environments")
            return False
            
        # Setup models (using main environment)
        activate_cmd = "source .venv-main/bin/activate"
        if not run_command(f"{activate_cmd} && python3 -c 'import sys; print(sys.executable)'"):
            logger.error("Failed to activate main environment")
            return False
            
        if not setup_models():
            logger.error("Failed to setup models")
            return False
            
        # Build Docker images
        if not build_docker_images():
            logger.error("Failed to build Docker images")
            return False
            
        # Start services
        if not start_docker_services():
            logger.error("Failed to start Docker services")
            return False
            
        # Verify services
        if not verify_services():
            logger.error("Failed to verify services")
            return False
            
        logger.info("Setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 