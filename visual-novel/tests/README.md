# Japanese Learning Visual Novel - Tests

This directory contains unit tests for the Japanese Learning Visual Novel application.

## Running Tests

To run all tests, use the following command from this directory:

```bash
python run_tests.py
```

Or to run individual test files:

```bash
python -m unittest test_api_service.py
python -m unittest test_jlpt_curriculum.py
python -m unittest test_progress_tracker.py
```

## Test Files

- `test_api_service.py`: Tests for the API service that communicates with external services
- `test_jlpt_curriculum.py`: Tests for the JLPT curriculum module
- `test_progress_tracker.py`: Tests for the progress tracking module
- `run_tests.py`: Script to run all tests

## Adding New Tests

When adding new features to the application, please add corresponding tests to ensure functionality works as expected. Follow these guidelines:

1. Create a new test file if testing a new module
2. Use the `unittest` framework for consistency
3. Mock external dependencies to avoid actual API calls during testing
4. Add the new test to `run_tests.py` to include it in the test suite

## Test Coverage

The tests aim to cover:

- API service functionality and error handling
- JLPT curriculum data structure and access methods
- Progress tracking and persistence

Future improvements could include:

- Integration tests for the server API endpoints
- End-to-end tests for the complete application flow
- Performance tests for resource-intensive operations