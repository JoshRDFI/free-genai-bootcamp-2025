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
        # Always use bash for commands that need source
        if 'source' in command:
            # Use double quotes for outer shell and single quotes for inner command
            command = f'bash -c "source {command.split("source ", 1)[1]}"'
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

def cleanup_venvs():
    """Remove all existing virtual environments."""
    logger.info("Cleaning up existing virtual environments...")
    venv_dirs = [
        ".venv-main",
        ".venv-ls",
        ".venv-vocab",
        ".venv-wp",
        ".venv-vn",
        ".venv-portal"
    ]
    
    for venv_dir in venv_dirs:
        venv_path = Path(venv_dir)
        if venv_path.exists():
            logger.info(f"Removing {venv_dir}...")
            try:
                shutil.rmtree(venv_path)
                logger.info(f"Successfully removed {venv_dir}")
            except Exception as e:
                logger.error(f"Error removing {venv_dir}: {e}")
                return False
    return True

def check_gpu_availability():
    """Check if GPU is available and compatible with PyTorch"""
    try:
        # First check if NVIDIA driver is available
        nvidia_smi = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True
        )
        if nvidia_smi.returncode != 0:
            logger.warning("NVIDIA driver not found. System will run in CPU mode.")
            return False
            
        # Get GPU info from nvidia-smi
        gpu_info = nvidia_smi.stdout
        logger.info(f"Detected GPU info:\n{gpu_info}")
        
        # Try to import torch and check CUDA availability
        import torch
        if not torch.cuda.is_available():
            logger.warning("CUDA not available in PyTorch despite NVIDIA driver being present.")
            logger.warning("This could be due to:")
            logger.warning("1. Incompatible GPU architecture")
            logger.warning("2. Incompatible CUDA version")
            logger.warning("3. PyTorch not built with CUDA support")
            logger.warning("System will run in CPU mode.")
            return False
            
        # Check CUDA version and compatibility
        cuda_version = torch.version.cuda
        logger.info(f"PyTorch CUDA version: {cuda_version}")
        
        # Get GPU compute capability
        try:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # Convert to GB
            compute_capability = torch.cuda.get_device_capability(0)
            logger.info(f"GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            logger.info(f"Compute Capability: {compute_capability[0]}.{compute_capability[1]}")
            
            # Check if compute capability is supported
            if compute_capability[0] < 7:  # PyTorch typically requires compute capability 7.0 or higher
                logger.warning(f"GPU compute capability {compute_capability[0]}.{compute_capability[1]} may not be fully supported.")
                logger.warning("Some operations may fall back to CPU or fail.")
                return False
                
        except Exception as e:
            logger.warning(f"Could not get detailed GPU information: {e}")
            logger.warning("Proceeding with basic GPU support.")
        
        # Try a simple CUDA operation to verify functionality
        try:
            x = torch.rand(5, 3).cuda()
            y = torch.rand(5, 3).cuda()
            z = x + y  # Simple CUDA operation
            del x, y, z  # Clean up
            torch.cuda.empty_cache()
            logger.info("CUDA functionality verified successfully")
        except Exception as e:
            logger.warning(f"CUDA functionality test failed: {e}")
            logger.warning("System will run in CPU mode.")
            return False
            
        return True
        
    except ImportError:
        logger.warning("PyTorch not installed. System will run in CPU mode.")
        return False
    except Exception as e:
        logger.warning(f"Error checking GPU availability: {e}. System will run in CPU mode.")
        return False

def setup_environment():
    """Set up the environment variables for GPU/CPU mode"""
    gpu_available = check_gpu_availability()
    
    if gpu_available:
        logger.info("GPU detected and verified compatible, configuring for GPU mode")
        os.environ["DOCKER_RUNTIME"] = "nvidia"
        os.environ["GPU_DRIVER"] = "nvidia"
        os.environ["GPU_COUNT"] = "all"
        os.environ["FORCE_CPU"] = "false"
    else:
        logger.info("No compatible GPU detected, configuring for CPU mode")
        os.environ["DOCKER_RUNTIME"] = "runc"
        os.environ["GPU_DRIVER"] = "none"
        os.environ["GPU_COUNT"] = "0"
        os.environ["FORCE_CPU"] = "true"

def install_pytorch(venv_python):
    """Install PyTorch with appropriate CUDA support in a virtual environment."""
    logger.info(f"Installing PyTorch using {venv_python}...")
    
    # Check if we should use CPU or GPU version
    if os.environ.get("FORCE_CPU", "false").lower() == "true":
        logger.info("Installing CPU-only version of PyTorch")
        pytorch_cmd = f"{venv_python} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
    else:
        logger.info("Installing CUDA-enabled version of PyTorch")
        pytorch_cmd = f"{venv_python} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    
    if not run_command(pytorch_cmd):
        logger.error("Failed to install PyTorch")
        return False
    return True

def setup_venv(venv_name, requirements_file=None, cwd=None):
    """Setup a virtual environment and install requirements."""
    logger.info(f"Setting up virtual environment: {venv_name}")
    
    try:
        # Get absolute paths
        root_dir = os.path.abspath(os.curdir)
        
        if cwd:
            # Get absolute paths for project directory
            project_dir = os.path.abspath(cwd)
            venv_path = os.path.join(project_dir, venv_name)
            
            # Create venv in the project directory
            if not run_command(f"python3 -m venv {venv_name}", cwd=project_dir):
                logger.error(f"Failed to create virtual environment: {venv_name} in {cwd}")
                return False
                
            # Install setuptools first
            venv_python = os.path.join(venv_path, "bin", "python")
            if not run_command(f"{venv_python} -m pip install --upgrade pip setuptools wheel", cwd=project_dir):
                logger.error(f"Failed to install setuptools in {venv_name}")
                return False
            
            # Install base requirements first
            base_req_path = os.path.join(root_dir, "requirements", "base.txt")
            if not run_command(f"{venv_python} -m pip install -r {base_req_path}", cwd=project_dir):
                logger.error(f"Failed to install base requirements in {venv_name}")
                return False
            
            # Install main requirements
            main_req_path = os.path.join(root_dir, "requirements", "main.txt")
            if not run_command(f"{venv_python} -m pip install -r {main_req_path}", cwd=project_dir):
                logger.error(f"Failed to install main requirements in {venv_name}")
                return False
                
            # Install project-specific requirements if specified
            if requirements_file:
                # Use root directory for requirements files
                req_path = os.path.join(root_dir, requirements_file)
                if not run_command(f"{venv_python} -m pip install -r {req_path}", cwd=project_dir):
                    logger.error(f"Failed to install project requirements in {venv_name}")
                    return False
        else:
            # Handle root directory venv
            venv_path = os.path.join(root_dir, venv_name)
            
            # Create venv in the root directory
            if not run_command(f"python3 -m venv {venv_name}", cwd=root_dir):
                logger.error(f"Failed to create virtual environment: {venv_name}")
                return False
                
            # Install setuptools first
            venv_python = os.path.join(venv_path, "bin", "python")
            if not run_command(f"{venv_python} -m pip install --upgrade pip setuptools wheel", cwd=root_dir):
                logger.error(f"Failed to install setuptools in {venv_name}")
                return False
            
            # Install base requirements first
            base_req_path = os.path.join(root_dir, "requirements", "base.txt")
            if not run_command(f"{venv_python} -m pip install -r {base_req_path}", cwd=root_dir):
                logger.error(f"Failed to install base requirements in {venv_name}")
                return False
            
            # Install main requirements
            main_req_path = os.path.join(root_dir, "requirements", "main.txt")
            if not run_command(f"{venv_python} -m pip install -r {main_req_path}", cwd=root_dir):
                logger.error(f"Failed to install main requirements in {venv_name}")
                return False
                
            # Install project-specific requirements if specified
            if requirements_file:
                req_path = os.path.join(root_dir, requirements_file)
                if not run_command(f"{venv_python} -m pip install -r {req_path}", cwd=root_dir):
                    logger.error(f"Failed to install project requirements in {venv_name}")
                    return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error setting up virtual environment {venv_name}: {e}")
        return False

def setup_environments():
    """Setup all virtual environments."""
    logger.info("Setting up virtual environments...")
    
    # Main environment (for project_start.py)
    if not setup_venv(".venv-main"):
        return False
        
    # Listening-Speaking environment
    if not setup_venv(".venv-ls", "listening-speaking/extra-requirements.txt", "listening-speaking"):
        return False
        
    # Vocabulary Generator environment
    if not setup_venv(".venv-vocab", "vocabulary_generator/extra-requirements.txt", "vocabulary_generator"):
        return False
        
    # Writing Practice environment
    if not setup_venv(".venv-wp", "writing-practice/requirements.txt", "writing-practice"):
        return False
        
    # Visual Novel server environment
    if not setup_venv(".venv-vn", "visual-novel/server/requirements.txt", "visual-novel/server"):
        return False
        
    # Lang Portal environment - multi-step process
    # 1. Create the virtual environment in lang-portal root
    if not setup_venv(".venv-portal", "lang-portal/extra-requirements.txt", "lang-portal"):
        return False
        
    # 2. Ensure Node.js and npm are installed (for frontend)
    if not run_command("command -v node >/dev/null 2>&1 || (sudo apt-get update && sudo apt-get install -y nodejs npm)", check=False):
        logger.warning("Failed to verify or install Node.js and npm. The lang-portal frontend may not work correctly.")
        
    # 3. Make setup.sh executable and run it within the virtual environment
    if not run_command("chmod +x setup.sh && source .venv-portal/bin/activate && ./setup.sh", cwd="lang-portal"):
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
        "lang-portal": (".venv-portal", "lang-portal")  # Updated to use root lang-portal directory
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
        "docker_services": ["llm", "tts", "asr", "embeddings", "chromadb", "guardrails", "mangaocr", "llava"],
        "requires_gpu": True
    },
    "vocabulary_generator": {
        "name": "Vocabulary Generator",
        "venv": ".venv-vocab",
        "run_command": "cd vocabulary_generator && {python} -m streamlit run main.py --server.port 8503",
        "docker_services": ["llm", "embeddings", "chromadb", "guardrails", "mangaocr", "llava"],
        "requires_gpu": True
    },
    "writing-practice": {
        "name": "Writing Practice",
        "venv": ".venv-wp",
        "run_command": "cd writing-practice && {python} -m streamlit run run_app.py --server.port 8504",
        "docker_services": ["llm", "mangaocr", "llava", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "visual-novel": {
        "name": "Visual Novel",
        "venv": ".venv-vn",
        "run_command": "cd visual-novel && {python} app.py",
        "docker_services": ["llm", "tts", "asr", "mangaocr", "llava", "embeddings", "chromadb", "guardrails", "waifu-diffusion"],
        "requires_gpu": True
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
        "mangaocr"
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
    
    if run_command("pip install --user -r requirements.txt"):
        return True
    
    logger.error("Could not install packages. Please ensure pip is installed:")
    logger.error("sudo apt update && sudo apt install python3-pip")
    return False

def check_cuda_installation():
    """Check if CUDA is properly installed and accessible."""
    try:
        # Check NVIDIA driver
        nvidia_smi = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True
        )
        if nvidia_smi.returncode != 0:
            logger.error("NVIDIA driver not found. Please install NVIDIA drivers first.")
            return False
            
        # Check CUDA version
        nvcc = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True,
            text=True
        )
        if nvcc.returncode != 0:
            logger.error("CUDA toolkit not found. Please install CUDA toolkit.")
            return False
            
        logger.info("CUDA installation verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error checking CUDA installation: {e}")
        return False

def install_cuda():
    """Install CUDA 12.8 if not already installed."""
    try:
        # Check if CUDA is already installed
        if check_cuda_installation():
            return True
            
        logger.info("Installing CUDA 12.8...")
        
        # Add NVIDIA package repositories
        if not run_command("wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin"):
            return False
            
        if not run_command("sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600"):
            return False
            
        if not run_command("wget https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/cuda-repo-ubuntu2204-12-8-local_12.8.0-525.85.05-1_amd64.deb"):
            return False
            
        if not run_command("sudo dpkg -i cuda-repo-ubuntu2204-12-8-local_12.8.0-525.85.05-1_amd64.deb"):
            return False
            
        if not run_command("sudo cp /var/cuda-repo-ubuntu2204-12-8-local/cuda-*-keyring.gpg /usr/share/keyrings/"):
            return False
            
        # Update and install CUDA
        if not run_command("sudo apt-get update"):
            return False
            
        if not run_command("sudo apt-get -y install cuda-12-8"):
            return False
            
        # Add CUDA to PATH
        cuda_path = "/usr/local/cuda-12.8/bin"
        if cuda_path not in os.environ["PATH"]:
            with open(os.path.expanduser("~/.bashrc"), "a") as f:
                f.write(f'\nexport PATH={cuda_path}:$PATH\n')
                f.write('export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH\n')
            
        logger.info("CUDA 12.8 installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error installing CUDA: {e}")
        return False

def main():
    """Main setup function."""
    try:
        # Set up environment variables first
        setup_environment()
        
        # Clean up existing virtual environments
        if not cleanup_venvs():
            logger.error("Failed to clean up existing virtual environments")
            return False
            
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
        main_venv_python = get_venv_python(".venv-main")
        if not run_command(f"{main_venv_python} download_models.py"):
            logger.error("Failed to download models")
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