#!/usr/bin/env python3
import os
import sys
import pytest
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_test_environment():
    """Set up the test environment"""
    # Ensure we're in the correct directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Create test data directory if it doesn't exist
    test_data_dir = project_root / 'tests' / 'test_data'
    test_data_dir.mkdir(exist_ok=True)
    
    # Set up environment variables for testing
    os.environ['TESTING'] = 'true'
    os.environ['TEST_DB_PATH'] = str(test_data_dir / 'test.db')
    os.environ['TEST_CONFIG_PATH'] = str(test_data_dir / 'test_config.json')

def run_tests():
    """Run all tests with pytest"""
    start_time = datetime.now()
    logging.info(f"Starting test run at {start_time}")
    
    # Configure pytest arguments
    pytest_args = [
        'tests',  # Directory containing tests
        '-v',     # Verbose output
        '--tb=short',  # Shorter traceback format
        '--cov=src',   # Measure code coverage for src directory
        '--cov-report=term-missing',  # Show missing lines in coverage report
        '--cov-report=html:coverage_report',  # Generate HTML coverage report
        '--junitxml=test_results.xml',  # Generate JUnit XML report
        '-p', 'no:warnings',  # Disable warning capture
    ]
    
    try:
        # Run the tests
        exit_code = pytest.main(pytest_args)
        
        # Log results
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Test run completed in {duration}")
        
        if exit_code == 0:
            logging.info("All tests passed successfully!")
        else:
            logging.error(f"Tests failed with exit code {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logging.error(f"Error running tests: {str(e)}")
        return 1

def cleanup_test_environment():
    """Clean up test environment"""
    try:
        # Remove test database if it exists
        test_db = Path(os.environ['TEST_DB_PATH'])
        if test_db.exists():
            test_db.unlink()
        
        # Remove test config if it exists
        test_config = Path(os.environ['TEST_CONFIG_PATH'])
        if test_config.exists():
            test_config.unlink()
            
        logging.info("Test environment cleaned up successfully")
    except Exception as e:
        logging.error(f"Error cleaning up test environment: {str(e)}")

def main():
    """Main function to run the test suite"""
    try:
        setup_test_environment()
        exit_code = run_tests()
        cleanup_test_environment()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 