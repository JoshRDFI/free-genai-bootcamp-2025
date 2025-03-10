# database/utils/init_sample_data.py
import sqlite3
from pathlib import Path
import logging

# Configure paths based on project layout
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db.sqlite3"
SAMPLE_DATA = [
    {
        "group": {"name": "Basic Greetings", "level": "N5"},
        "words": [
            ("こんにちは", "konnichiwa", "Hello"),
            ("ありがとう", "arigatou", "Thank you"),
            ("おはよう", "ohayou", "Good morning"),
        ]
    },
    {
        "group": {"name": "Common Verbs", "level": "N4"},
        "words": [
            ("食べる", "taberu", "To eat"),
            ("飲む", "nomu", "To drink"),
            ("行く", "iku", "To go"),
        ]
    }
]

def initialize_sample_data():
    """Insert sample data into existing database tables"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            for category in SAMPLE_DATA:
                # Insert word group
                cursor.execute(
                    "INSERT INTO word_groups (name, level) VALUES (?, ?)",
                    (category["group"]["name"], category["group"]["level"])
                )
                group_id = cursor.lastrowid

                # Insert words
                cursor.executemany(
                    """INSERT INTO words
                    (kanji, romaji, english, group_id)
                    VALUES (?, ?, ?, ?)""",
                    [(w[0], w[1], w[2], group_id) for w in category["words"]]
                )

            conn.commit()
            print(f"Successfully inserted {len(SAMPLE_DATA)} categories with sample words")

    except sqlite3.Error as e:
        logging.error(f"Database error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"Initializing sample data in {DB_PATH}")
    initialize_sample_data()