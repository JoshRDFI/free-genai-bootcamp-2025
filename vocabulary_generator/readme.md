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