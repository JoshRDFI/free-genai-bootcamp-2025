# Visual Novel Tests

This directory contains all tests and utility scripts for the Visual Novel project.

## Test Files

### Core Tests
- **`test_api_service.py`** - Unit tests for API service functionality
- **`test_env_and_server.py`** - Tests .env file loading and server connectivity
- **`test_progress_tracker.py`** - Tests for progress tracking functionality
- **`test_jlpt_curriculum.py`** - Tests for JLPT curriculum functionality

### Utility Scripts
- **`copy_env_to_web.py`** - Copies .env file to web build directory
- **`run_all_tests.py`** - Comprehensive test runner for all tests and utilities

### Legacy Tests
- **`test_services.py`** - Legacy service tests
- **`test_timeout.py`** - Legacy timeout tests
- **`run_tests.py`** - Legacy test runner

## Usage

### Running All Tests
```bash
# From the visual-novel directory
python3 tests/run_all_tests.py
```

### Running Individual Tests
```bash
# Test environment and server connectivity
python3 tests/test_env_and_server.py

# Run API service tests
python3 tests/test_api_service.py

# Copy .env file to web build
python3 tests/copy_env_to_web.py
```

### Post-Build Setup
After rebuilding with Ren'Py, run the post-build setup:
```bash
# From the visual-novel directory
python3 post_build_setup.py
```

This will:
1. Check if the web build exists
2. Copy the .env file to the web build directory
3. Provide next steps for testing

## Test Structure

### Environment Tests
- **`test_env_and_server.py`** - Verifies that:
  - .env file can be loaded correctly
  - Environment variables are set properly
  - Server endpoints are accessible
  - API calls work correctly

### API Service Tests
- **`test_api_service.py`** - Tests the API service module including:
  - Web request handling
  - Request queue system
  - Error handling
  - Response processing

### Utility Scripts
- **`copy_env_to_web.py`** - Ensures .env file is available in web build
- **`run_all_tests.py`** - Orchestrates running all tests with proper reporting

## Workflow

### After Ren'Py Rebuild
1. Delete the old web build files
2. Rebuild with Ren'Py
3. Run post-build setup: `python3 post_build_setup.py`
4. Test the application

### Regular Testing
1. Run all tests: `python3 tests/run_all_tests.py`
2. Check for any failures
3. Fix issues and re-test

## Notes

- The .env file must be copied to the web build directory after each Ren'Py rebuild
- Tests are designed to work both in development and web environments
- The queue system prevents concurrent fetch requests in web environments
- All tests include proper error handling and debugging output