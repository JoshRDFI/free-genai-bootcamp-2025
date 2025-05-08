# Troubleshooting Guide

If you're having trouble starting the API server, here are some common issues and solutions:

## Python Command Not Found

If you see an error like `python: command not found`, it means that Python is either not installed or not in your PATH.

### Solutions:

1. **Check if Python is installed**:
   - On Linux/Mac: Run `which python3` or `which python`
   - On Windows: Run `where python` or `where python3`

2. **Install Python if needed**:
   - Download and install Python 3 from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation on Windows

3. **Use the correct Python command**:
   - On many systems, Python 3 is accessed using the `python3` command instead of `python`
   - Try running `python3 server.py` instead of `python server.py`

4. **Use the direct run scripts**:
   - Try using `run_direct.sh` (Linux/Mac) or `run_direct.bat` (Windows) which attempt to find the correct Python command

## Virtual Environment Issues

If you're having trouble with the virtual environment:

### Solutions:

1. **Install virtualenv**:
   ```
   pip install virtualenv
   ```

2. **Skip the virtual environment**:
   - Use the direct run scripts: `run_direct.sh` or `run_direct.bat`
   - Or run the server directly: `python3 server.py` or `python server.py`

## Permission Issues (Linux/Mac)

If you're getting permission errors:

### Solutions:

1. **Make scripts executable**:
   ```
   chmod +x *.sh
   chmod +x server.py
   ```
   
   Or run the provided script:
   ```
   bash make_executable.sh
   ```

2. **Run with sudo if needed**:
   ```
   sudo ./start_api.sh
   ```

## Flask Not Installed

If you see an error about Flask not being installed:

### Solutions:

1. **Install Flask manually**:
   ```
   pip install flask
   ```
   or
   ```
   python -m pip install flask
   ```
   or
   ```
   python3 -m pip install flask
   ```

## Port 5000 Already in Use

If port 5000 is already in use:

### Solutions:

1. **Find and stop the process using port 5000**:
   - On Linux/Mac: `lsof -i :5000` to find the process, then `kill <PID>` to stop it
   - On Windows: `netstat -ano | findstr :5000` to find the process, then `taskkill /PID <PID> /F` to stop it

2. **Change the port in server.py**:
   - Open `server.py` and change the port number in the last line:
     ```python
     app.run(host='0.0.0.0', port=5001, debug=True)  # Changed from 5000 to 5001
     ```
   - Then update the main application to use the new port

## Database Issues

If you're having issues with the database:

### Solutions:

1. **Check database path**:
   - Make sure the `data` directory exists in the parent directory
   - Create it manually if needed: `mkdir -p ../data`

2. **Check database permissions**:
   - Make sure the user running the API has write permissions to the data directory

## Still Having Issues?

If you're still having issues:

1. **Check the logs**:
   - Look for error messages in the console output
   - Check the log file in the data directory if it exists

2. **Run with debug output**:
   - Modify `server.py` to print more debug information
   - Add `print` statements to help identify where the issue is occurring

3. **Try a minimal test**:
   - Create a simple Flask app to test if Flask is working correctly:
     ```python
     from flask import Flask
     app = Flask(__name__)
     
     @app.route('/')
     def hello():
         return "Hello, World!"
     
     if __name__ == '__main__':
         app.run(debug=True)
     ```