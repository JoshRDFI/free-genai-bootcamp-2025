# Japanese Vocabulary Generator

A comprehensive Japanese vocabulary learning system that helps users learn and practice Japanese vocabulary through various interactive features and study tools.

## Features

- **Vocabulary Management**
  - Generate vocabulary entries with kanji, romaji, and English translations
  - JLPT level-based organization (N5 to N1)
  - Example sentence generation
  - Word grouping and categorization
  - Import vocabulary from JSON files

- **Study Tools**
  - Interactive typing tutor for practicing romaji input
  - Flashcard-style review system
  - Adventure MUD game mode for engaging vocabulary practice
  - Progress tracking and statistics
  - Study session management

- **User Experience**
  - Clean, intuitive Streamlit interface
  - Real-time feedback on answers
  - Progress visualization
  - Session statistics
  - JLPT level progression system

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone the repository:
```bash
git clone https://github.com/yourusername/vocabulary_generator.git
cd vocabulary_generator
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

1. Start the Streamlit application:
```bash
streamlit run main.py
```

2. The application will open in your default web browser.

### Using the Vocabulary Generator

1. **User Stats and History**
   - View your current JLPT level
   - Check total study sessions and reviews
   - Monitor your accuracy
   - Track study time
   - View progression history

2. **Vocabulary Import**
   - Import core vocabulary from JSON files
   - Words are automatically categorized and organized

3. **Study Sessions**
   Choose from three study modes:
   - **Typing Tutor**: Practice typing the romaji for Japanese words
   - **Flashcards**: Review words in a traditional flashcard format
   - **Adventure MUD**: Play a text-based adventure game while learning vocabulary
     - Collect ingredients for "The Ultimate Bowl of Ramen"
     - Solve word challenges to progress
     - Earn ingredients for correct answers

4. **Session Management**
   - Start new study sessions
   - Select word groups to study
   - Track progress within sessions
   - End sessions when complete

### Study Session Flow

1. Click "Start New Study Session"
2. Select your preferred study mode (Typing Tutor, Flashcards, or Adventure MUD)
3. Choose a word group to study
4. Complete the session:
   - For Typing Tutor: Type the romaji for each word
   - For Flashcards: Review words and mark them as known/unknown
   - For Adventure MUD: Solve word challenges to collect ramen ingredients
5. View your session results
6. End the session when complete

## Configuration

The application uses a configuration file (`config/config.json`) for:
- Database settings
- API endpoints
- Storage paths
- JLPT level requirements
- Study session parameters

## Project Structure

See `project-layout.txt` for the complete project structure.

## Development

### Adding New Features

1. Create new modules in the `src` directory
2. Add corresponding tests in the `tests` directory
3. Update configuration if needed
4. Run tests to ensure compatibility

### Testing

The project uses pytest for testing. Run tests with:
```bash
python run_tests.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Japanese language resources
- Open source contributors
- Streamlit framework
- Testing framework developers