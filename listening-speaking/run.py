# run.py

import os
import subprocess
import sys
import argparse
import sqlite3
from setup_env import setup_environment
import threading
import logging
import socket

def install_dependencies():
    """Install required dependencies"""
    try:
        # Install requirements
        requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        sys.exit(1)

def run_streamlit():
    """Run the Streamlit app"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Streamlit app path
        streamlit_app = os.path.join(project_root, "frontend", "streamlit_app.py")

        # Run Streamlit
        subprocess.run(["streamlit", "run", streamlit_app])
    except Exception as e:
        print(f"Error running Streamlit app: {str(e)}")
        sys.exit(1)

def check_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except:
        return False

def run_backend():
    """Run the backend FastAPI server"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Set required environment variables
        backend_port = 8000
        os.environ["BACKEND_PORT"] = str(backend_port)
        os.environ["LLM_TEXT_PORT"] = "9000"
        os.environ["TTS_SERVICE_PORT"] = "9200"
        os.environ["ASR_SERVICE_PORT"] = "9300"
        os.environ["LLM_VISION_PORT"] = "9100"
        os.environ["EMBEDDING_SERVICE_PORT"] = "6000"
        os.environ["WAIFU_DIFFUSION_PORT"] = "9500"
        
        # Set TTS data path if not already set
        if "TTS_DATA_PATH" not in os.environ:
            tts_data_path = os.path.join(os.path.dirname(project_root), "data", "tts_data")
            os.environ["TTS_DATA_PATH"] = tts_data_path

        # Add the project root to Python path
        sys.path.insert(0, project_root)

        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(project_root, "backend", "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, "backend.log")),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)

        # Check if port is available
        if not check_port_available(backend_port):
            logger.error(f"Port {backend_port} is already in use. Please free up the port and try again.")
            sys.exit(1)

        # Import and run uvicorn directly
        try:
            import uvicorn
            from backend.app import app

            logger.info("Starting backend server...")
            
            # Run uvicorn with proper configuration
            uvicorn.run(
                "backend.app:app",  # Use import string for reload to work
                host="0.0.0.0",
                port=backend_port,
                log_level="debug",
                reload=True,
                reload_dirs=[os.path.join(project_root, "backend")],  # Only watch backend directory
                timeout_keep_alive=30,  # Increase keep-alive timeout
                access_log=True,  # Enable access logging
                use_colors=False  # Disable colors for better log parsing
            )
        except ImportError as e:
            logger.error(f"Failed to import required modules: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to start backend server: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error running backend: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def log_process_output(process, name):
    """Log process output"""
    try:
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"{name}: {line.strip()}")
            
            error_line = process.stderr.readline()
            if error_line:
                print(f"{name} error: {error_line.strip()}")
    except Exception as e:
        print(f"Error in log_process_output: {str(e)}")

def get_database_paths():
    """Get possible database paths from environment or default locations"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Get custom path from environment variable if set
    custom_db_path = os.getenv('APP_DATABASE_PATH')
    
    db_paths = [
        os.path.join(project_root, "backend", "database", "knowledge_base.db"),
    ]
    
    if custom_db_path:
        db_paths.insert(0, custom_db_path)
        
    return db_paths

def check_database_exists():
    """Check if database already exists in the correct location"""
    db_paths = get_database_paths()
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                # Try to connect to the database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Check if our tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
                if cursor.fetchone():
                    conn.close()
                    return True
            except sqlite3.Error:
                continue
    return False

def setup_database():
    """Set up the database"""
    try:
        # Check if database already exists
        if check_database_exists():
            print("Database and tables already exist. Skipping setup.")
            return

        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Setup script path
        setup_script = os.path.join(project_root, "setup", "setup_db.py")

        # Run setup script
        subprocess.run(["python3", setup_script], check=True)
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Always run environment setup first
    if not setup_environment():
        print("Error: Environment setup failed. Please check the error messages above.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Run the JLPT Listening Practice application")
    parser.add_argument("--setup", action="store_true", help="Set up the database and environment")
    parser.add_argument("--backend", action="store_true", help="Run the backend server")
    parser.add_argument("--frontend", action="store_true", help="Run the Streamlit frontend")
    parser.add_argument("--env-only", action="store_true", help="Only set up the environment")

    args = parser.parse_args()

    # Install dependencies first
    install_dependencies()

    if args.env_only:
        # Environment already set up, just exit
        sys.exit(0)
    elif args.setup:
        setup_database()
    elif args.backend:
        run_backend()
    elif args.frontend:
        run_streamlit()
    else:
        print("Please specify an action: --setup, --backend, or --frontend")
        sys.exit(1)