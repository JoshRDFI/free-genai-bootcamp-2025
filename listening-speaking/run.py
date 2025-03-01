# run.py

import os
import subprocess
import sys
import argparse

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
        subprocess.run(["python", backend_app])
    except Exception as e:
        print(f"Error running backend: {str(e)}")
        sys.exit(1)

def setup_database():
    """Set up the database"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Setup script path
        setup_script = os.path.join(project_root, "setup", "setup_db.py")

        # Run setup script
        subprocess.run(["python", setup_script])
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the JLPT Listening Practice application")
    parser.add_argument("--setup", action="store_true", help="Set up the database")
    parser.add_argument("--backend", action="store_true", help="Run the backend server")
    parser.add_argument("--frontend", action="store_true", help="Run the Streamlit frontend")

    args = parser.parse_args()

    if args.setup:
        setup_database()
    elif args.backend:
        run_backend()
    elif args.frontend:
        run_streamlit()
    else:
        print("Please specify an action: --setup, --backend, or --frontend")
        sys.exit(1)