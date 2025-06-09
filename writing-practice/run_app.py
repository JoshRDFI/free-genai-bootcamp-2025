#!/usr/bin/env python3
"""
Startup script for the Japanese Writing Practice application.
This script starts the Streamlit app when run independently.
"""

import os
import sys
import subprocess
import time
import signal
import logging
import webbrowser
from pathlib import Path
import threading

# ---- Path Configuration ----
BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent

# ---- Logging Configuration ----
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables for process management
app_process = None

def monitor_process_output(process, name):
    """Monitor process output in a background thread"""
    def read_output(pipe, log_func):
        for line in pipe:
            log_func(f"{name}: {line.strip()}")
    
    if process.stdout:
        threading.Thread(target=read_output, 
                        args=(process.stdout, logger.info),
                        daemon=True).start()
    if process.stderr:
        threading.Thread(target=read_output, 
                        args=(process.stderr, logger.error),
                        daemon=True).start()

def start_streamlit_app():
    """Start the Streamlit app"""
    global app_process
    
    logger.info("Starting Streamlit app...")
    
    try:
        # Change to base directory
        os.chdir(BASE_DIR)
        logger.info(f"Changed to base directory: {BASE_DIR}")
        
        # Start Streamlit app with port 8504
        app_process = subprocess.Popen([
            str(BASE_DIR / ".venv-wp" / "bin" / "python3"),
            "-m", "streamlit", "run", "app.py",
            "--server.port", "8504"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # Start monitoring process output
        monitor_process_output(app_process, "Streamlit")
        
        # Wait a moment for Streamlit to start
        logger.info("Waiting for Streamlit to start...")
        time.sleep(2)
        
        # Check if process is running
        if app_process.poll() is None:
            logger.info("App process started successfully")
            # Open browser to Streamlit
            webbrowser.open("http://localhost:8504")
            return True
        else:
            logger.error(f"App process failed to start - exited with code {app_process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start app: {e}")
        return False

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    logger.info("Cleaning up processes...")
    
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
    print("Starting Japanese Writing Practice application...")  # Immediate console feedback
    
    # Register signal handlers for graceful shutdown only in main thread
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
    
    logger.info("Starting Japanese Writing Practice application...")
    
    # Start Streamlit app
    print("Starting Streamlit app...")  # Immediate console feedback
    app_started = start_streamlit_app()
    if not app_started:
        print("Failed to start Streamlit app. Exiting.")
        logger.error("Failed to start Streamlit app. Exiting.")
        cleanup()
        return 1
    
    print("Application started successfully")
    logger.info("Application started successfully")
    
    try:
        # Keep the script running to manage the processes
        while True:
            time.sleep(1)
            
            # Check if process is still running
            if app_process and app_process.poll() is not None:
                logger.error(f"Streamlit app process terminated unexpectedly with code {app_process.returncode}")
                cleanup()
                return 1
                
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
        logger.info("Received keyboard interrupt")
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())