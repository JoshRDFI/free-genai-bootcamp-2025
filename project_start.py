import streamlit as st
import subprocess
import os
import time
import requests
import json
from pathlib import Path
import docker
from PIL import Image
import sys
import logging
import webbrowser
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed back to INFO to reduce noise
    format='%(asctime)s - %(levelname)s - %(message)s',  # Simplified format
    handlers=[
        logging.FileHandler("project_launcher.log", mode='w'),  # 'w' mode to start fresh each time
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce logging from other modules
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('docker').setLevel(logging.WARNING)
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

def check_backend_health():
    """Check if backend service is healthy"""
    try:
        # First check if LLM service is running
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
        if not ("message" in llm_data and llm_data["done"] == True):
            logger.error("LLM service not responding correctly")
            return False

        # Then check if backend API is running
        backend_response = requests.get("http://localhost:8000/health")
        if backend_response.status_code != 200:
            logger.error(f"Backend API returned status {backend_response.status_code}")
            return False

        return True
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error checking services: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error checking services: {str(e)}")
        return False

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

def setup_tts_requirements():
    """Install TTS setup requirements."""
    try:
        requirements_path = os.path.join("opea-docker", "setup_requirements.txt")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error installing TTS requirements: {str(e)}")
        return False

def setup_tts():
    """Run the TTS setup script."""
    try:
        setup_script = os.path.join("opea-docker", "setup_tts.py")
        result = subprocess.run([sys.executable, setup_script], capture_output=True, text=True)
        if result.returncode != 0:
            st.error(f"TTS setup failed: {result.stderr}")
            return False
        return True
    except Exception as e:
        st.error(f"Error running TTS setup: {str(e)}")
        return False

def check_tts_files():
    """Check if TTS model files exist."""
    tts_data_dir = Path("data/tts_data")
    required_files = [
        "config.json",
        "model.pth",
        "vocab.json",
        "speakers_xtts_v2.pth",
        "speaker_embeddings.pth"
    ]
    
    if not tts_data_dir.exists():
        return False
    
    return all((tts_data_dir / file).exists() for file in required_files)

# Project configurations
PROJECTS = {
    "listening-speaking": {
        "name": "Listening & Speaking Practice",
        "description": "Practice listening and speaking with AI feedback",
        "run_command": "cd listening-speaking && python3 run.py --setup && python3 run.py --backend && streamlit run frontend/streamlit_app.py --server.port 8502",
        "docker_services": ["llm", "tts", "asr", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "vocabulary_generator": {
        "name": "Vocabulary Generator and Practice Excercises",
        "description": "Generate vocabulary lists and practice exercises",
        "run_command": "cd vocabulary_generator && streamlit run main.py --server.port 8503",
        "docker_services": ["llm", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "writing-practice": {
        "name": "Writing Practice",
        "description": "Practice writing with AI feedback",
        "run_command": "cd writing-practice && streamlit run run_app.py --server.port 8504",
        "docker_services": ["llm", "vision", "embeddings", "chromadb", "guardrails"],
        "requires_gpu": True
    },
    "visual-novel": {
        "name": "Visual Novel",
        "description": "Interactive story with AI-generated content",
        "run_command": "cd visual-novel && python3 app.py",
        "docker_services": ["llm", "tts", "asr", "vision", "embeddings", "chromadb", "guardrails", "waifu-diffusion"],
        "requires_gpu": True
    }
}

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
            st.info("Setting up TTS service...")
            if not setup_tts_requirements():
                st.error("Failed to install TTS requirements")
                return False
            if not setup_tts():
                st.error("Failed to download TTS model files")
                return False
            st.success("TTS setup completed successfully!")

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
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
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

        # Check TTS model files if TTS service is required
        if "tts" in project.get('docker_services', []):
            tts_data_dir = Path("data/tts_data")
            required_tts_files = [
                "config.json",
                "model.pth",
                "vocab.json",
                "speakers_xtts_v2.pth",
                "speaker_embeddings.pth"
            ]
            
            if not tts_data_dir.exists():
                return False, "TTS model files not found. Please run setup_tts.py first."
            
            missing_files = [f for f in required_tts_files if not (tts_data_dir / f).exists()]
            if missing_files:
                return False, f"Missing TTS model files: {', '.join(missing_files)}. Please run setup_tts.py first."

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
                    ["python3", "run.py", "--setup"],
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
                
                # Kill any existing process on port 8000
                try:
                    subprocess.run(["fuser", "-k", "8000/tcp"], capture_output=True)
                except:
                    pass  # Ignore if fuser is not available
                
                backend_cmd = ["python3", "run.py", "--backend"]
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
                        PYTHONPATH=os.path.abspath("listening-speaking")  # Add project root to Python path
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
                frontend_process = subprocess.Popen(
                    ["streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8502"],
                    cwd="listening-speaking",
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
                    http://localhost:8502
                    
                    Note: If you can't access the application, make sure:
                    1. You're using the Windows browser (not WSL)
                    2. The port 8502 is not blocked by your firewall
                    3. You're using 'localhost' and not the WSL IP address
                    """)
                else:
                    st.info(f"The application should open in your browser. If it doesn't, you can access it at: http://localhost:8502")
                return True
            else:
                # For other projects, run the command directly
                process = subprocess.Popen(
                    project['run_command'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                project['processes'] = [process]
                
                # Wait a moment and check if process is still running
                time.sleep(2)
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise Exception(f"Failed to start {project_name}: {stderr}")
                
                # For Streamlit apps, provide URL information
                if "streamlit" in project['run_command']:
                    # Extract port from run command
                    port = "8501"  # default port
                    if "--server.port" in project['run_command']:
                        port = project['run_command'].split("--server.port")[1].strip().split()[0]
                    
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

def main():
    """
    # Set background image -- uncomment when a good image is found.
    try:
        background_image = Image.open("writing-practice/images/1240417.png")
        st.image(background_image, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load background image: {str(e)}")
    """
    st.title("🎓 JLPT5 Language Tutor Launcher")
    
    # Check Docker services
    if not verify_services(["llm", "tts", "asr", "vision"]):
        st.warning("Docker services are not running. Starting services...")
        if start_docker_services():
            st.success("Docker services started successfully!")
        else:
            st.error("Failed to start Docker services. Please check Docker installation.")
            return

    # Project selection
    st.header("Select a Project")
    
    for project_id, project in PROJECTS.items():
        with st.container():
            st.markdown(f"""
                <div class="project-card">
                    <h3>{project['name']}</h3>
                    <p>{project['description']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Launch {project['name']}", key=f"launch_{project_id}"):
                # For visual novel, check both sets of services
                if project_id == "visual-novel":
                    if not verify_services(project['docker_services'], project.get('vn_services')):
                        st.warning("Starting visual novel services...")
                        if not start_docker_services(project_id):
                            st.error("Failed to start visual novel services.")
                            return
                else:
                    if not verify_services(project['docker_services']):
                        st.error("Required services are not running. Please try again.")
                        return
                
                if run_project(project_id):
                    st.success(f"Launched {project['name']}!")
                else:
                    st.error(f"Failed to launch {project['name']}")

    # Exit option
    if st.button("Exit All"):
        st.warning("This will stop all running projects. Docker services will remain running.")
        if st.button("Confirm Exit", key="confirm_exit"):
            # Add cleanup code here if needed
            st.success("All projects stopped. Docker services are still running.")
            st.stop()

if __name__ == "__main__":
    main()
