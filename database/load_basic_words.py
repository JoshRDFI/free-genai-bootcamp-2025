import sqlite3
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.absolute()
DB_PATH = BASE_DIR / "db.sqlite3"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Sample words for each category
categories = [
    {"name": "Basic Starter Words", "level": "N5", "words": [
        ("こんにちは", "konnichiwa", "Hello"),
        ("ありがとう", "arigatou", "Thank you"),
        ("さようなら", "sayounara", "Goodbye")
    ]},
    {"name": "Daily Life", "level": "N4", "words": [
        ("朝ごはん", "asagohan", "Breakfast"),
        ("昼ごはん", "hirugohan", "Lunch"),
        ("晩ごはん", "bangohan", "Dinner")
    ]},
    {"name": "Travel", "level": "N3", "words": [
        ("飛行機", "hikouki", "Airplane"),
        ("ホテル", "hoteru", "Hotel"),
        ("観光", "kankou", "Sightseeing")
    ]},
    {"name": "Work", "level": "N2", "words": [
        ("会議", "kaigi", "Meeting"),
        ("報告", "houkoku", "Report"),
        ("プロジェクト", "purojekuto", "Project")
    ]},
    {"name": "Advanced", "level": "N1", "words": [
        ("哲学", "tetsugaku", "Philosophy"),
        ("経済", "keizai", "Economy"),
        ("政治", "seiji", "Politics")
    ]}
]

# Insert categories and words
for category in categories:
    cursor.execute(
        "INSERT INTO word_groups (name, level) VALUES (?, ?)",
        (category["name"], category["level"])
    )
    group_id = cursor.lastrowid
    for word in category["words"]:
        cursor.execute(
            "INSERT INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
            (word[0], word[1], word[2], group_id)
        )

# Commit changes and close connection
conn.commit()
conn.close()

print("Basic words loaded successfully.")