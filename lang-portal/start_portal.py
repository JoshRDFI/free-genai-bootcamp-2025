#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import threading
from typing import Optional, Tuple
from backend.db.init_db import init_db

class ServerProcess:
    def __init__(self, name: str):
        self.name = name
        self.process: Optional[subprocess.Popen] = None
        self.output_thread: Optional[threading.Thread] = None

    def _log_output(self, stream, prefix: str) -> None:
        """Log output from a stream with a prefix."""
        for line in stream:
            if line.strip():
                print(f"{prefix} {line.strip()}")

    def start(self, command: list[str], cwd: Optional[str] = None) -> None:
        """Start a server process with the given command."""
        print(f"Starting {self.name} server...")
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            bufsize=1,
            universal_newlines=True
        )

        # Start threads to capture and display output
        if self.process.stdout:
            self.output_thread = threading.Thread(
                target=self._log_output,
                args=(self.process.stdout, f"[{self.name}]"),
                daemon=True
            )
            self.output_thread.start()

        if self.process.stderr:
            threading.Thread(
                target=self._log_output,
                args=(self.process.stderr, f"[{self.name} ERROR]"),
                daemon=True
            ).start()

    def is_running(self) -> bool:
        """Check if the process is still running."""
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        """Stop the process if it's running."""
        if self.process:
            print(f"Stopping {self.name} server...")
            self.process.terminate()
            self.process.wait()
            if self.output_thread:
                self.output_thread.join(timeout=1)

class LanguagePortal:
    def __init__(self):
        self.backend = ServerProcess("backend")
        self.frontend = ServerProcess("frontend")

    def install_frontend_dependencies(self) -> None:
        """Install frontend dependencies."""
        print("Installing frontend dependencies...")
        process = subprocess.Popen(
            ["npm", "install"],
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Capture and display output
        if process.stdout:
            threading.Thread(
                target=self._log_output,
                args=(process.stdout, "[npm install]"),
                daemon=True
            ).start()
        
        if process.stderr:
            threading.Thread(
                target=self._log_output,
                args=(process.stderr, "[npm install ERROR]"),
                daemon=True
            ).start()
        
        process.wait()
        if process.returncode != 0:
            raise RuntimeError("Failed to install frontend dependencies")

    def _log_output(self, stream, prefix: str) -> None:
        """Log output from a stream with a prefix."""
        for line in stream:
            if line.strip():
                print(f"{prefix} {line.strip()}")

    def start_servers(self) -> None:
        """Initialize and start both servers."""
        print("Initializing database...")
        init_db()

        # Start backend
        self.backend.start([
            sys.executable, "-m", "uvicorn",
            "backend.api.main:app",
            "--host", "0.0.0.0",
            "--port", "5000"
        ])
        time.sleep(2)  # Wait for backend to initialize

        # Install frontend dependencies and start frontend
        self.install_frontend_dependencies()
        self.frontend.start(
            ["npm", "run", "dev"],
            cwd="frontend"
        )
        time.sleep(5)  # Wait for frontend to initialize

    def display_instructions(self) -> None:
        """Display instructions for accessing the application."""
        print("\nLanguage Portal is running!")
        print("\nTo access the application:")
        print("1. Open your host machine's browser")
        print("2. Navigate to http://localhost:5173")
        print("\nPress Ctrl+C to stop both servers")

    def monitor_servers(self) -> None:
        """Monitor server processes and handle their status."""
        while True:
            if not self.backend.is_running():
                print("Backend server stopped unexpectedly")
                break
            
            if not self.frontend.is_running():
                print("Frontend server stopped unexpectedly")
                break
            
            time.sleep(1)

    def cleanup(self) -> None:
        """Clean up server processes."""
        print("\nCleaning up...")
        self.backend.stop()
        self.frontend.stop()

    def run(self) -> None:
        """Run the language portal application."""
        try:
            self.start_servers()
            self.display_instructions()
            self.monitor_servers()
        except KeyboardInterrupt:
            print("\nStopping servers...")
        finally:
            self.cleanup()

def main():
    portal = LanguagePortal()
    portal.run()

if __name__ == "__main__":
    main() 