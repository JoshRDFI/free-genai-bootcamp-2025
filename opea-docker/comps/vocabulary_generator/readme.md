# Japanese Vocabulary Generator

A comprehensive Japanese vocabulary learning system that helps users learn and practice Japanese vocabulary through various interactive features and study tools.

## Features

- **Vocabulary Management**
  - Generate vocabulary entries with kanji, romaji, and English translations
  - JLPT level-based organization
  - Example sentence generation
  - Word grouping and categorization

- **Study Tools**
  - Interactive typing tutor
  - Sentence practice
  - Progress tracking
  - Achievement system
  - Study session scheduling

- **User Experience**
  - Personalized study reminders
  - Progress visualization
  - Customizable preferences
  - Level progression system
  - Achievement tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vocabulary_generator.git
cd vocabulary_generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install test dependencies (optional):
```bash
pip install -r requirements-test.txt
```

## Usage

### Running the Application

Start the Streamlit application:
```bash
streamlit run main.py
```

### Running Tests

Run the test suite:
```bash
python run_tests.py
```

This will:
- Run all tests
- Generate coverage reports
- Create test logs
- Clean up test resources

## Configuration

The application can be configured through the `config/default_config.json` file. Key configuration options include:

- Database settings
- API endpoints
- Study session parameters
- User preferences defaults
- JLPT level requirements

## Development

### Project Structure

See `project-layout.txt` for the complete project structure.

### Adding New Features

1. Create new modules in the `src` directory
2. Add corresponding tests in the `tests` directory
3. Update configuration if needed
4. Run tests to ensure compatibility

### Testing

The project uses pytest for testing. Key testing features include:

- Async test support
- Coverage reporting
- Parallel test execution
- Test data management
- Mocking and environment control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Japanese language resources
- Open source contributors
- Testing framework developers