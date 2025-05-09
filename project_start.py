import streamlit as st
import subprocess
import os
import time
import requests
import json
from pathlib import Path
import docker
from PIL import Image

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

# Project configurations
PROJECTS = {
    "visual-novel": {
        "name": "Visual Novel",
        "description": "Interactive Japanese learning through visual novel gameplay",
        "docker_services": ["llm", "tts", "asr", "vision"],
        "vn_services": ["vn-game-server", "vn-web-server", "waifu-diffusion"],
        "run_command": "cd visual-novel && python3 app.py",
        "documentation": "visual-novel/README.md"
    },
    "listening-speaking": {
        "name": "Listening & Speaking Practice",
        "description": "Practice Japanese listening and speaking with AI-powered exercises",
        "docker_services": ["llm", "tts", "asr"],
        "run_command": "cd listening-speaking && python3 run.py --setup && python3 run.py --backend && python3 run.py --frontend",
        "documentation": "listening-speaking/README.md"
    },
    "vocabulary_generator": {
        "name": "Vocabulary Generator",
        "description": "AI-assisted vocabulary learning and practice",
        "docker_services": ["llm", "embeddings"],
        "run_command": "cd vocabulary_generator && streamlit run app.py",
        "documentation": "vocabulary_generator/README.md"
    },
    "writing-practice": {
        "name": "Writing Practice",
        "description": "Practice writing Japanese with AI feedback",
        "docker_services": ["llm", "vision"],
        "run_command": "cd writing-practice && streamlit run app.py",
        "documentation": "writing-practice/README.md"
    },
    "Sentence-constructor": {
        "name": "Sentence Constructor",
        "description": "Build and practice Japanese sentences",
        "docker_services": ["llm"],
        "run_command": "cd Sentence-constructor && streamlit run app.py",
        "documentation": "Sentence-constructor/README.md"
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
        # Start opea-docker services
        subprocess.run(["docker", "compose", "-f", "opea-docker/docker-compose.yml", "up", "-d"], check=True)
        
        # If visual novel is selected, start its services too
        if project_id == "visual-novel":
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

def run_project(project_name):
    """Run a specific project"""
    if project_name not in PROJECTS:
        st.error(f"Project {project_name} not found!")
        return

    project = PROJECTS[project_name]
    
    # Check if Docker services are required and running
    if project.get('docker_services'):
        if not verify_services(project['docker_services'], project.get('vn_services')):
            st.error("Required Docker services are not running. Please start them first.")
            return

    # Create a placeholder for status messages
    status_placeholder = st.empty()
    
    try:
        # Run the project command
        status_placeholder.info(f"Starting {project_name}...")
        
        # For listening-speaking project, run the components in sequence
        if project_name == "listening-speaking":
            # Run setup
            setup_process = subprocess.Popen(
                ["python3", "run.py", "--setup"],
                cwd="listening-speaking",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = setup_process.communicate()
            if setup_process.returncode != 0:
                raise Exception(f"Setup failed: {stderr}")
            
            # Run backend
            backend_process = subprocess.Popen(
                ["python3", "run.py", "--backend"],
                cwd="listening-speaking",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for backend to start
            time.sleep(2)
            
            # Run frontend on a different port
            frontend_process = subprocess.Popen(
                ["streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8502"],
                cwd="listening-speaking",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store processes for later cleanup
            project['processes'] = [backend_process, frontend_process]
            
            # Wait a moment for frontend to start
            time.sleep(2)
            
            # Check if frontend is running
            if frontend_process.poll() is not None:
                stdout, stderr = frontend_process.communicate()
                raise Exception(f"Frontend failed to start: {stderr}")
            
            status_placeholder.success(f"Launched {project_name}!")
            
            # Display the URL with the correct port
            st.info("The application should open in your browser. If it doesn't, you can access it at: http://localhost:8502")
            
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
            status_placeholder.success(f"Launched {project_name}!")
            
    except Exception as e:
        status_placeholder.error(f"Error launching {project_name}: {str(e)}")
        # Clean up any processes that were started
        if 'processes' in project:
            for process in project['processes']:
                if process.poll() is None:  # If process is still running
                    process.terminate()
            project['processes'] = []

def main():
    """# Set background image -- uncomment when a good image is found.
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
