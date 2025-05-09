# run.py

import os
import subprocess
import sys
import argparse
import sqlite3
from setup_env import setup_environment

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

def run_backend():
    """Run the backend FastAPI server"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Backend app path
        backend_app = os.path.join(project_root, "backend", "app.py")

        # Run backend
        subprocess.run(["python3", backend_app])
    except Exception as e:
        print(f"Error running backend: {str(e)}")
        sys.exit(1)

def check_database_exists():
    """Check if database already exists in shared location"""
    shared_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "opea-docker", "data", "shared_db", "shared.db")
    if os.path.exists(shared_db_path):
        try:
            # Try to connect to the database
            conn = sqlite3.connect(shared_db_path)
            cursor = conn.cursor()
            # Check if our tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            if cursor.fetchone():
                conn.close()
                return True
        except sqlite3.Error:
            pass
    return False

def setup_database():
    """Set up the database"""
    try:
        # Check if database already exists
        if check_database_exists():
            print("Database already exists in shared location. Skipping setup.")
            return

        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Setup script path
        setup_script = os.path.join(project_root, "setup", "setup_db.py")

        # Run setup script
        subprocess.run(["python3", setup_script])
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the JLPT Listening Practice application")
    parser.add_argument("--setup", action="store_true", help="Set up the database and environment")
    parser.add_argument("--backend", action="store_true", help="Run the backend server")
    parser.add_argument("--frontend", action="store_true", help="Run the Streamlit frontend")
    parser.add_argument("--env-only", action="store_true", help="Only set up the environment")

    args = parser.parse_args()

    # Install dependencies first
    install_dependencies()

    if args.env_only:
        setup_environment()
    elif args.setup:
        # Set up environment first
        if setup_environment():
            setup_database()
    elif args.backend:
        run_backend()
    elif args.frontend:
        run_streamlit()
    else:
        print("Please specify an action: --setup, --backend, --frontend, or --env-only")
        sys.exit(1)