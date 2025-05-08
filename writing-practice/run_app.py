#!/usr/bin/env python3
"""
Startup script for the Japanese Writing Practice application.
This script starts both the API server and the Streamlit app.
"""

import os
import sys
import subprocess
import time
import signal
import logging
import webbrowser
from pathlib import Path
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('startup')

# Paths
BASE_DIR = Path(__file__).parent.absolute()
API_DIR = BASE_DIR / "api"
DATA_DIR = BASE_DIR / "data"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Global variables for process management
api_process = None
app_process = None

def is_port_in_use(port):
    """Check if a port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_api_server():
    """Start the API server"""
    global api_process
    
    logger.info("Starting API server...")
    
    # Check if API is already running
    if is_port_in_use(5000):
        logger.info("API server is already running on port 5000")
        return True
    
    try:
        # Change to API directory
        os.chdir(API_DIR)
        
        # Determine which script to run based on OS
        if platform.system() == "Windows":
            if os.path.exists("start_api.bat"):
                api_process = subprocess.Popen(["start_api.bat"], 
                                              shell=True,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            else:
                # Direct Python execution if batch file not available
                api_process = subprocess.Popen([sys.executable, "server.py"],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
        else:  # Linux/Mac
            if os.path.exists("start_api.sh"):
                # Make sure the script is executable
                os.chmod("start_api.sh", 0o755)
                api_process = subprocess.Popen(["./start_api.sh"],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            else:
                # Direct Python execution if shell script not available
                api_process = subprocess.Popen([sys.executable, "server.py"],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
        
        # Change back to base directory
        os.chdir(BASE_DIR)
        
        # Wait for API to start
        logger.info("Waiting for API server to start...")
        max_attempts = 10
        for i in range(max_attempts):
            if is_port_in_use(5000):
                logger.info("API server started successfully")
                return True
            time.sleep(1)
            
        logger.warning(f"API server did not start after {max_attempts} seconds")
        return False
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return False

def start_streamlit_app():
    """Start the Streamlit app"""
    global app_process
    
    logger.info("Starting Streamlit app...")
    
    try:
        # Change to base directory
        os.chdir(BASE_DIR)
        
        # Start Streamlit app
        app_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        
        # Wait a moment for Streamlit to start
        time.sleep(2)
        
        # Open browser
        webbrowser.open("http://localhost:8501")
        
        logger.info("Streamlit app started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {e}")
        return False

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    logger.info("Cleaning up processes...")
    
    if api_process:
        logger.info("Terminating API server...")
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
    
    if app_process:
        logger.info("Terminating Streamlit app...")
        app_process.terminate()
        try:
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_process.kill()
    
    logger.info("Cleanup complete")
    
    if signum:
        sys.exit(0)

def main():
    """Main function"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    logger.info("Starting Japanese Writing Practice application...")
    
    # Start API server
    api_started = start_api_server()
    if not api_started:
        logger.error("Failed to start API server. Exiting.")
        cleanup()
        return 1
    
    # Start Streamlit app
    app_started = start_streamlit_app()
    if not app_started:
        logger.error("Failed to start Streamlit app. Exiting.")
        cleanup()
        return 1
    
    logger.info("Application started successfully")
    
    try:
        # Keep the script running to manage the processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                logger.error("API server process terminated unexpectedly")
                cleanup()
                return 1
            
            if app_process and app_process.poll() is not None:
                logger.error("Streamlit app process terminated unexpectedly")
                cleanup()
                return 1
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())