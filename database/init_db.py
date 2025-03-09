#!/usr/bin/env python3
import sqlite3
import os
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent  # Root directory of the project
DATA_DIR = BASE_DIR / "data"  # Data directory
DB_PATH = DATA_DIR / "db.sqlite3"  # Database path
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"  # Schema file path

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

print(f"Initializing database at {DB_PATH}...")
print(f"Using schema from {SCHEMA_PATH}")

# Read schema file
with open(SCHEMA_PATH, 'r') as f:
    schema = f.read()

# Connect to database and execute schema
conn = sqlite3.connect(DB_PATH)
try:
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Execute the schema script
    # Note: executescript automatically commits if successful
    conn.executescript(schema)
    print("Database schema successfully applied!")
except sqlite3.Error as e:
    print(f"Error applying schema: {e}")
    # If there was an error, try to execute statements one by one to identify the problem
    print("Attempting to execute statements individually to identify the issue...")
    conn2 = sqlite3.connect(DB_PATH)
    conn2.execute("PRAGMA foreign_keys = ON;")
    
    # Split the schema into individual statements
    statements = schema.split(';')
    for i, statement in enumerate(statements):
        statement = statement.strip()
        if statement:  # Skip empty statements
            try:
                conn2.execute(statement + ';')
                conn2.commit()
            except sqlite3.Error as e2:
                print(f"Error in statement {i+1}: {e2}")
                print(f"Statement: {statement}")
                break
    conn2.close()
finally:
    conn.close()

print("Database initialization complete.")