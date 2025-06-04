#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def check_venv():
    """Check if we're running in the correct virtual environment."""
    venv_path = Path(".venv-main")
    if not venv_path.exists():
        print("""
Error: Virtual environment not found. This could mean either:
1. You haven't run first_start.py yet (for first-time setup)
2. The virtual environment was deleted

Please run first_start.py for first-time setup:
    python3 first_start.py

If you've already run first_start.py before, please ensure the .venv-main directory exists.
""")
        sys.exit(1)

    # Get the path to the virtual environment's Python
    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        print("Error: Virtual environment Python not found. Please run first_start.py again.")
        sys.exit(1)

    # Check if we're running in the correct Python
    # More flexible check that allows for symlinks and different path formats
    venv_python_real = os.path.realpath(str(venv_python))
    current_python_real = os.path.realpath(sys.executable)
    
    if venv_python_real != current_python_real:
        print(f"""
Error: Please run this script using the Python from the virtual environment:
    {venv_python} {__file__}

Or use the launcher script:
    ./launch.sh
""")
        sys.exit(1)

# Check virtual environment before any imports
if __name__ == "__main__":
    check_venv()

# Now we can safely import the rest of the modules
import streamlit as st
import subprocess
import time
import requests
import json
import docker
from PIL import Image
import logging
import webbrowser
import threading
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("project_launcher.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce logging from other modules
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('docker').setLevel(logging.WARNING)
logging.getLogger('torch').setLevel(logging.WARNING)

# Project configurations
PROJECTS = {
    "listening-speaking": {
        "name": "Listening & Speaking Practice",
        "description": "Practice listening and speaking with AI feedback",
        "docker_services": ["llm_text", "tts", "asr", "embeddings", "chromadb", "guardrails", "mangaocr", "llm-vision"],
        "requires_gpu": True,
        "run_command": "listening-speaking/frontend streamlit_app.py 8502"
    },
    "vocabulary_generator": {
        "name": "Vocabulary Generator and Practice Exercises",
        "description": "Generate vocabulary lists and practice exercises",
        "docker_services": ["llm_text", "embeddings", "chromadb", "guardrails", "mangaocr", "llm-vision"],
        "requires_gpu": True,
        "run_command": "vocabulary_generator main.py 8503"
    },
    "writing-practice": {
        "name": "Writing Practice",
        "description": "Practice writing with AI feedback",
        "docker_services": ["llm_text", "mangaocr", "llm-vision", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True,
        "run_command": "writing-practice run_app.py 8504"
    },
    "visual-novel": {
        "name": "Visual Novel",
        "description": "Interactive story with AI-generated content",
        "docker_services": ["llm_text", "tts", "asr", "mangaocr", "llm-vision", "embeddings", "chromadb", "guardrails", "waifu-diffusion"],
        "requires_gpu": True,
        "run_command": "visual-novel app.py 8505"
    }
}

def check_backend_health():
    """Check if backend service is healthy (parallelized)"""
    import threading
    results = {}

    def check_llm():
        try:
            test_request = {
                "messages": [{"role": "user", "content": "test"}],
                "model": "llama3.2"
            }
            headers = {"Content-Type": "application/json"}
            llm_response = requests.post(
                "http://localhost:9000/v1/chat/completions",
                json=test_request,
                headers=headers,
                timeout=10
            )
            llm_data = llm_response.json()
            results['llm'] = ("message" in llm_data and llm_data.get("done") == True)
        except Exception as e:
            logger.error(f"LLM service not responding correctly: {str(e)}")
            results['llm'] = False

    def check_mangaocr():
        try:
            mangaocr_response = requests.get("http://localhost:9000/health", timeout=30)
            results['mangaocr'] = (mangaocr_response.status_code == 200)
        except Exception as e:
            logger.error(f"MangaOCR service not available: {str(e)}")
            results['mangaocr'] = False

    def check_llava():
        try:
            llava_response = requests.get("http://localhost:9101/health", timeout=60)
            results['llava'] = (llava_response.status_code == 200)
        except Exception as e:
            logger.error(f"LLaVA service not available: {str(e)}")
            results['llava'] = False

    def check_backend():
        try:
            backend_response = requests.get("http://localhost:8180/health", timeout=30)
            results['backend'] = (backend_response.status_code == 200)
        except Exception as e:
            logger.error(f"Backend API not available: {str(e)}")
            results['backend'] = False

    threads = [
        threading.Thread(target=check_llm),
        threading.Thread(target=check_mangaocr),
        threading.Thread(target=check_llava),
        threading.Thread(target=check_backend)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return all(results.get(k, False) for k in ['llm', 'mangaocr', 'llava', 'backend'])

def log_process_output(process, name):
    """Log process output"""
    try:
        while True:
            # Read stdout
            stdout_line = process.stdout.readline()
            if stdout_line:
                print(f"{name}: {stdout_line.strip()}")
            
            # Read stderr
            stderr_line = process.stderr.readline()
            if stderr_line:
                print(f"{name} error: {stderr_line.strip()}")
            
            # Check if process has ended
            if process.poll() is not None:
                # Read any remaining output
                for line in process.stdout:
                    print(f"{name}: {line.strip()}")
                for line in process.stderr:
                    print(f"{name} error: {line.strip()}")
                break
                
    except Exception as e:
        print(f"Error in log_process_output: {str(e)}")
        import traceback
        traceback.print_exc()

def check_tts_files():
    """Check if TTS model files exist."""
    tts_data_dir = Path("data/tts_data/tts/tts_models--multilingual--multi-dataset--xtts_v2")
    # XTTS V2 model directory as per download_models.py
    if not tts_data_dir.exists() or not any(tts_data_dir.iterdir()):
        return False
    return True

def get_venv_python(project_name):
    """Get the Python interpreter path for a project's virtual environment."""
    venv_mapping = {
        "listening-speaking": (".venv-ls", "listening-speaking"),
        "vocabulary_generator": (".venv-vocab", "vocabulary_generator"),
        "writing-practice": (".venv-wp", "writing-practice"),
        "visual-novel": (".venv-vn", "visual-novel"),
        "lang-portal": (".venv-portal", "lang-portal/backend")
    }
    
    if project_name in venv_mapping:
        venv_name, project_dir = venv_mapping[project_name]
        # Use absolute path
        venv_path = Path(os.path.abspath(project_dir)) / venv_name
        python_path = venv_path / "bin" / "python3"
        if not python_path.exists():
            logger.error(f"Python interpreter not found at: {python_path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Absolute venv path: {venv_path}")
        return str(python_path)
    return sys.executable  # Fallback to system Python

def get_venv_streamlit(project_name):
    """Get the streamlit command from a project's virtual environment."""
    venv_mapping = {
        "listening-speaking": (".venv-ls", "listening-speaking"),
        "vocabulary_generator": (".venv-vocab", "vocabulary_generator"),
        "writing-practice": (".venv-wp", "writing-practice")
    }
    
    if project_name in venv_mapping:
        venv_name, project_dir = venv_mapping[project_name]
        venv_path = Path(project_dir) / venv_name
        
        # Check if virtual environment exists
        if not venv_path.exists():
            logger.error(f"Virtual environment {venv_name} not found")
            return "streamlit"
            
        # Check if streamlit is installed in the virtual environment
        streamlit_path = venv_path / "bin" / "streamlit"
        if not streamlit_path.exists():
            logger.info(f"Installing streamlit in {venv_name}...")
            try:
                python_path = venv_path / "bin" / "python"
                subprocess.run([str(python_path), "-m", "pip", "install", "streamlit"], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install streamlit: {e}")
                return "streamlit"
        
        return str(streamlit_path.resolve())
    return "streamlit"  # Fallback to system streamlit

def check_docker_service(service_name):
    """Check if a specific Docker service is running"""
    try:
        client = docker.from_env()
        containers = client.containers.list(filters={"name": service_name})
        return len(containers) > 0
    except Exception as e:
        st.error(f"Error checking Docker service {service_name}: {str(e)}")
        return False

def start_docker_services(project_id=None):
    """Start the Docker services using docker compose"""
    try:
        # Check if TTS files are present
        if not check_tts_files():
            st.error("TTS model files are missing. Please run './launch.sh' or 'python3 download_models.py' to download the required models before starting the project.")
            return False

        # Start opea-docker services first
        st.info("Starting main services...")
        subprocess.run(["docker", "compose", "-f", "opea-docker/docker-compose.yml", "up", "-d"], check=True)
        
        # Wait for services to be fully up
        time.sleep(5)
        
        # If visual novel is selected, start its services too
        if project_id == "visual-novel":
            st.info("Starting visual novel services...")
            # Ensure the network exists
            try:
                subprocess.run(["docker", "network", "create", "opea-docker_default"], check=False)
            except subprocess.CalledProcessError:
                # Network might already exist, which is fine
                pass
            
            subprocess.run(["docker", "compose", "-f", "visual-novel/docker/docker-compose.yml", "up", "-d"], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error starting Docker services: {str(e)}")
        return False

def verify_services(required_services, vn_services=None):
    """Verify that all required services are running"""
    # Check opea-docker services
    for service in required_services:
        if not check_docker_service(service):
            return False
    
    # Check visual novel services if specified
    if vn_services:
        for service in vn_services:
            if not check_docker_service(service):
                return False
    
    return True

def check_gpu_availability():
    """Check if GPU is available and return True if it is"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def validate_project(project_name: str, project: dict) -> tuple[bool, str]:
    """
    Validate project setup before launching.
    Returns (is_valid, error_message)
    """
    try:
        # Check if project directory exists
        if not os.path.exists(project_name):
            return False, f"Project directory '{project_name}' not found"

        # Install project-specific requirements if they exist
        requirements_file = os.path.join(project_name, "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                # Get the correct Python interpreter for this project
                python_cmd = get_venv_python(project_name)
                if not os.path.exists(python_cmd):
                    return False, f"Virtual environment Python not found: {python_cmd}"
                
                # Install requirements using the project's virtual environment Python
                subprocess.run([python_cmd, "-m", "pip", "install", "-r", requirements_file], 
                             check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                return False, f"Failed to install project requirements: {e.stderr}"

        # Check for required files based on project type
        if project_name == "listening-speaking":
            required_files = [
                "run.py",
                "frontend/streamlit_app.py",
                "backend/app.py",
                "setup/setup_db.py"
            ]
        elif project_name == "vocabulary_generator":
            required_files = [
                "main.py"
            ]
        elif project_name == "writing-practice":
            required_files = [
                "run_app.py",
                "images"
            ]
        elif project_name == "visual-novel":
            required_files = [
                "app.py",
                "server",
                "renpy",
                "docker/docker-compose.yml"
            ]
        else:
            return False, f"Unknown project type: {project_name}"

        # Check each required file
        for file_path in required_files:
            full_path = os.path.join(project_name, file_path)
            if not os.path.exists(full_path):
                return False, f"Required file/directory not found: {full_path}"

        # Check for required Python packages
        if project_name in ["listening-speaking", "vocabulary_generator", "writing-practice"]:
            try:
                import streamlit
            except ImportError:
                return False, "Required package 'streamlit' not found. Please install it with: pip install streamlit"

        # Check for Docker if required
        if project.get('docker_services'):
            try:
                import docker
                client = docker.from_env()
                client.ping()
            except Exception as e:
                return False, f"Docker is required but not available: {str(e)}"

        # Check for GPU if required
        if project.get('requires_gpu'):
            gpu_available = check_gpu_availability()
            if not gpu_available:
                st.warning("GPU is not available. The application will run in CPU mode, which may be slower.")

        # Check if required Docker services are running
        if project.get('docker_services'):
            for service in project['docker_services']:
                if not check_docker_service(service):
                    return False, f"Required Docker service '{service}' is not running. Please start the Docker services first."

        return True, ""

    except Exception as e:
        return False, f"Error during project validation: {str(e)}"

def is_wsl():
    """Check if running in WSL"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False

def run_project(project_name):
    """Run a specific project"""
    if project_name not in PROJECTS:
        st.error(f"Project {project_name} not found!")
        return False

    project = PROJECTS[project_name]
    python_cmd = get_venv_python(project_name)
    streamlit_cmd = get_venv_streamlit(project_name)
    
    # Create a placeholder for status messages
    status_placeholder = st.empty()
    
    try:
        # Validate project setup first
        status_placeholder.info("Validating project setup...")
        is_valid, error_message = validate_project(project_name, project)
        if not is_valid:
            status_placeholder.error(f"Project validation failed: {error_message}")
            return False

        # Check if Docker services are required and start them if needed
        if project.get('docker_services'):
            status_placeholder.info("Checking required services...")
            if not verify_services(project['docker_services']):
                status_placeholder.info("Starting required Docker services...")
                if not start_docker_services(project_name):
                    st.error("Failed to start required Docker services.")
                    return False
                # Wait for services to be fully up
                time.sleep(5)
                if not verify_services(project['docker_services']):
                    st.error("Required Docker services are still not running after startup attempt.")
                    return False

        # Run the project command
        status_placeholder.info(f"Starting {project_name}...")
        
        try:
            # For listening-speaking practice, we need to handle it specially
            if project_name == "listening-speaking":
                # Set TTS_DATA_PATH environment variable
                tts_data_path = os.path.abspath("data/tts_data")
                os.environ["TTS_DATA_PATH"] = tts_data_path
                
                # Run setup
                status_placeholder.info("Running setup...")
                setup_process = subprocess.Popen(
                    [python_cmd, "run.py", "--setup"],
                    cwd="listening-speaking",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=dict(os.environ, TTS_DATA_PATH=tts_data_path)
                )
                stdout, stderr = setup_process.communicate()
                if setup_process.returncode != 0:
                    raise Exception(f"Setup failed: {stderr}")
                
                # Run backend
                status_placeholder.info("Starting backend...")
                logger.info("Starting backend process")
                
                # Kill any existing process on port 8180
                try:
                    subprocess.run(["fuser", "-k", "8180/tcp"], capture_output=True)
                except:
                    pass  # Ignore if fuser is not available
                
                backend_cmd = [python_cmd, "run.py", "--backend"]
                logger.info(f"Running command: {' '.join(backend_cmd)} in {os.path.abspath('listening-speaking')}")

                # Now start the actual backend process
                backend_process = subprocess.Popen(
                    backend_cmd,
                    cwd="listening-speaking",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=dict(os.environ,
                        TTS_DATA_PATH=tts_data_path,
                        LLM_SERVICE_URL="http://localhost:9000",
                        EMBEDDINGS_SERVICE_URL="http://localhost:6000",
                        PYTHONUNBUFFERED="1",  # Ensure Python output is not buffered
                        PYTHONPATH=os.path.abspath("listening-speaking"),  # Add project root to Python path
                        CHROMA_SERVER_PORT="8000"  # Match the port in docker-compose.yml
                    ),
                    bufsize=1,
                    universal_newlines=True
                )

                # Start backend logger thread
                backend_logger = threading.Thread(
                    target=log_process_output,
                    args=(backend_process, "Backend")
                )

                backend_logger.daemon = True
                backend_logger.start()
                logger.debug("Backend logger thread started")
                
                # Wait for backend to be healthy
                status_placeholder.info("Waiting for backend to be ready...")
                retries = 15  # Increased retries
                backend_started = False
                while retries > 0:
                    logger.debug(f"Checking backend health (attempts remaining: {retries})")
                    
                    # Check if process has terminated
                    if backend_process.poll() is not None:
                        stdout, stderr = backend_process.communicate()
                        logger.error("Backend process terminated unexpectedly")
                        logger.error(f"Exit code: {backend_process.returncode}")
                        logger.error(f"stdout: {stdout}")
                        logger.error(f"stderr: {stderr}")
                        raise Exception(f"Backend process terminated with exit code {backend_process.returncode}")
                    
                    # Check LLM service
                    try:
                        if check_backend_health():
                            backend_started = True
                            logger.info("Backend health check passed")
                            break
                    except Exception as e:
                        logger.debug(f"Health check failed (attempt {16-retries}/15): {str(e)}")
                    
                    logger.debug("Backend not ready yet, waiting...")
                    time.sleep(2)
                    retries -= 1
                
                if not backend_started:
                    logger.error("Backend failed to start within timeout period")
                    stdout, stderr = backend_process.communicate()
                    logger.error(f"Final stdout: {stdout}")
                    logger.error(f"Final stderr: {stderr}")
                    backend_process.terminate()
                    raise Exception("Backend failed to start properly")
                
                status_placeholder.info("Backend is ready!")
                logger.info("Backend startup completed successfully")
                
                # Run frontend on a different port
                status_placeholder.info("Starting frontend...")
                # Parse run_command for working directory, script, and port
                run_cmd = project['run_command'].split()
                frontend_work_dir = run_cmd[0]
                frontend_script = run_cmd[1]
                frontend_port = run_cmd[2] if len(run_cmd) > 2 else "8502"
                frontend_process = subprocess.Popen(
                    [streamlit_cmd, "run", frontend_script, "--server.port", frontend_port],
                    cwd=frontend_work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=dict(os.environ, 
                        TTS_DATA_PATH=tts_data_path,
                        LLM_SERVICE_URL="http://localhost:9000",
                        EMBEDDINGS_SERVICE_URL="http://localhost:6000"
                    ),
                    bufsize=1,
                    universal_newlines=True
                )

                # Start frontend logger thread
                frontend_logger = threading.Thread(
                    target=log_process_output,
                    args=(frontend_process, "Frontend")
                )
                frontend_logger.daemon = True
                frontend_logger.start()
                
                # Store processes for later cleanup
                project['processes'] = [backend_process, frontend_process]
                
                # Wait a moment for frontend to start
                time.sleep(2)
                
                # Check if frontend is running
                if frontend_process.poll() is not None:
                    stdout, stderr = frontend_process.communicate()
                    raise Exception(f"Frontend failed to start: {stderr}")
                
                status_placeholder.success(f"Launched {project_name}!")
                if is_wsl():
                    st.info(f"""
                    The application is running! Since you're using WSL, please open this URL in your Windows browser:
                    http://localhost:{frontend_port}
                    
                    Note: If you can't access the application, make sure:
                    1. You're using the Windows browser (not WSL)
                    2. The port {frontend_port} is not blocked by your firewall
                    3. You're using 'localhost' and not the WSL IP address
                    """)
                else:
                    st.info(f"The application should open in your browser. If it doesn't, you can access it at: http://localhost:{frontend_port}")
                return True
            else:
                # For other projects, run the command directly
                run_cmd = project['run_command'].split()
                work_dir = run_cmd[0]
                script_path = run_cmd[1]
                port = run_cmd[2] if len(run_cmd) > 2 else "8501"
                
                # Ensure the script exists
                if not os.path.exists(os.path.join(work_dir, script_path)):
                    raise Exception(f"Script not found: {os.path.join(work_dir, script_path)}")
                
                # Run the command
                process = subprocess.Popen(
                    [streamlit_cmd, "run", script_path, "--server.port", port],
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=dict(os.environ, PYTHONPATH=work_dir)  # Add project directory to Python path
                )
                project['processes'] = [process]
                
                # Wait a moment and check if process is still running
                time.sleep(2)
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise Exception(f"Failed to start {project_name}: {stderr}")
                
                # For Streamlit apps, provide URL information
                if is_wsl():
                    st.info(f"""
                    The application is running! Since you're using WSL, please open this URL in your Windows browser:
                    http://localhost:{port}
                    
                    Note: If you can't access the application, make sure:
                    1. You're using the Windows browser (not WSL)
                    2. The port {port} is not blocked by your firewall
                    3. You're using 'localhost' and not the WSL IP address
                    """)
                else:
                    st.info(f"The application should open in your browser. If it doesn't, you can access it at: http://localhost:{port}")
                
                status_placeholder.success(f"Launched {project_name}!")
                return True
            
        except Exception as e:
            status_placeholder.error(f"Error launching {project_name}: {str(e)}")
            if 'processes' in project:
                for process in project['processes']:
                    if process.poll() is None:
                        process.terminate()
                project['processes'] = []
            return False

    except Exception as e:
        status_placeholder.error(f"Unexpected error launching {project_name}: {str(e)}")
        return False

def set_background():
    """Set a background image for the Streamlit app."""
    try:
        # Try to use a background image if it exists
        bg_image = "assets/background.jpg"
        if os.path.exists(bg_image):
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/jpeg;base64,{base64.b64encode(open(bg_image, "rb").read()).decode()}");
                    background-attachment: fixed;
                    background-size: cover;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
    except Exception as e:
        logger.warning(f"Could not set background image: {str(e)}")

def main():
    """Main function to run the project launcher."""
    try:
        # Configure Streamlit page
        st.set_page_config(
            page_title="JLPT5 Language Tutor Launcher",
            page_icon="🎓",
            layout="wide"
        )

        # Custom CSS for better styling
        st.markdown("""
            <style>
            .main {
                background-color: rgba(255, 255, 255, 0.9);
            }
            .stButton>button {
                width: 100%;
                margin: 5px 0;
            }
            .project-card {
                padding: 20px;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.8);
                margin: 10px 0;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Set background image
        set_background()
        
        # Display header
        st.title("JLPT5 Language Tutor")
        st.markdown("Welcome to the JLPT5 Language Tutor! Choose a project to start:")
        
        # Create columns for project cards
        col1, col2 = st.columns(2)
        
        # Display project cards
        for i, (project_id, project) in enumerate(PROJECTS.items()):
            with col1 if i % 2 == 0 else col2:
                with st.container():
                    st.markdown(f"""
                    <div class="project-card">
                        <h3>{project['name']}</h3>
                        <p>{project['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add start button
                    if st.button(f"Start {project['name']}", key=project_id):
                        run_project(project_id)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
