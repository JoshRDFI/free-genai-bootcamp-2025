#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import webbrowser
import signal
import atexit

# Store process references
backend_process = None
frontend_process = None

def cleanup():
    """Cleanup function to stop both servers"""
    global backend_process, frontend_process
    
    if backend_process:
        print("Stopping backend server...")
        backend_process.terminate()
        backend_process.wait()
    
    if frontend_process:
        print("Stopping frontend server...")
        frontend_process.terminate()
        frontend_process.wait()

def signal_handler(signum, frame):
    """Handle termination signals"""
    print("\nReceived termination signal. Cleaning up...")
    cleanup()
    sys.exit(0)

# Register cleanup function
atexit.register(cleanup)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    global backend_process, frontend_process
    
    # Start backend server
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, "backend/main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Wait for backend to start
    time.sleep(2)
    
    # Start frontend server
    print("Starting frontend server...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    )
    
    # Wait for frontend to start
    time.sleep(5)
    
    # Open browser
    print("Opening browser...")
    webbrowser.open("http://localhost:5173")
    
    print("\nLanguage Portal is running!")
    print("Press Ctrl+C to stop both servers")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        cleanup()

if __name__ == "__main__":
    main() 