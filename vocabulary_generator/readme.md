vocabulary_generator/
├── config/
│   └── config.json       # Configuration settings
├── data/
│   ├── json_output/      # Generated JSON files
│   └── imports/          # Import source files
├── src/
│   ├── __init__.py
│   ├── generator.py      # Main generator class
│   ├── validator.py      # JLPT level validation
│   ├── converter.py      # Kanji/romaji conversion
│   ├── database.py       # Database operations
│   └── sentence_gen.py   # Example sentence generation
├── tests/
│   ├── __init__.py
│   ├── test_generator.py
│   ├── test_validator.py
│   ├── test_converter.py
│   ├── test_database.py
│   └── test_sentence_gen.py
└── main.py              # Entry point

# Japanese Language Learning System

## Overview
This project is a comprehensive Japanese language learning system designed to help students master JLPT N5 vocabulary through interactive study sessions and systematic progression tracking. The system consists of a FastAPI backend service that communicates with an ollama-server for AI-assisted content generation and a SQLite database for data persistence.

## Core Components

### Backend Services
- **FastAPI Application (opea-service)**: Handles HTTP requests and manages the application logic.
- **Ollama Server**: Provides AI capabilities for generating vocabulary content and example sentences.
- **SQLite Database**: Stores vocabulary, study sessions, and progression data.

### Key Modules
1. **VocabularyManager**: Central coordinator for all vocabulary-related operations.
   - Manages vocabulary entries.
   - Handles study sessions.
   - Tracks progression through JLPT levels.
   - Coordinates with other modules.

2. **Generator Module**: Creates vocabulary entries with AI assistance.
   - Generates vocabulary content.
   - Creates example sentences.
   - Validates JLPT level appropriateness.

3. **Validator Module**: Ensures data quality and JLPT level compliance.
   - Validates vocabulary entries.
   - Checks JLPT level requirements.
   - Maintains data consistency.

4. **Database Module**: Handles all database operations.
   - Manages word groups and vocabulary.
   - Tracks study sessions and reviews.
   - Records progression history.

5. **Converter Module**: Handles Japanese text conversions.
   - Manages kanji/kana conversions.
   - Provides romaji translations.

## Data Structure
- **Word Groups**: Collections of related vocabulary words.
- **Words**: Individual vocabulary entries with kanji, romaji, and English translations.
- **Study Sessions**: Records of learning activities.
- **Word Reviews**: Individual word assessment results.
- **Progression History**: Tracks advancement through JLPT levels.

## Features
- Vocabulary entry creation and management.
- Interactive study sessions.
- Progress tracking and level advancement.
- Example sentence generation.
- Data import/export capabilities.
- Student performance analytics.

## Database Schema
The system uses SQLite with the following main tables:
- `word_groups`: Organizes vocabulary into logical groups.
- `words`: Stores individual vocabulary entries.
- `study_sessions`: Records learning activities.
- `word_review_items`: Tracks individual word reviews.
- `progression_history`: Monitors JLPT level advancement.

## Configuration
The system uses a JSON configuration file (`config.json`) to manage:
- API endpoints.
- Database settings.
- JLPT progression criteria.
- Storage paths for JSON files.

## Usage
1. Import or create vocabulary groups.
2. Start study sessions.
3. Review words and track progress.
4. Advance through JLPT levels based on performance.

## Development Status

### Currently Implemented:
- Core vocabulary management system.
- Study session tracking.
- Progress monitoring.
- Basic JLPT level progression.

### Planned Features:
- Enhanced analytics.
- Additional study activities.
- Advanced progression tracking.

## Dependencies
- **FastAPI**
- **SQLite**
- **Requests**
- **PyKakasi**
- **Pytest** (for testing)