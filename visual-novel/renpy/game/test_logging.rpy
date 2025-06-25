# Test script for logging functionality
label test_logging:
    scene bg classroom
    
    python:
        log_debug("Test: Logging function is working")
        log_debug("Test: This should appear in debug.log")
    
    "Testing logging functionality..."
    
    python:
        log_debug("Test: Another log message")
    
    "Check the logs/debug.log file to see if these messages appear."
    
    return 