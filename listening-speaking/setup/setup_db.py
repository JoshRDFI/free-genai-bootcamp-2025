# setup/setup_db.py

import sqlite3
import os
import sys

def setup_database():
    """Set up the SQLite database with the schema"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Database path
        db_path = os.path.join(project_root, "backend", "database", "knowledge_base.db")

        # Schema path
        schema_path = os.path.join(project_root, "setup", "schema.sql")

        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(db_path)

        # Read schema file
        with open(schema_path, 'r') as f:
            schema = f.read()

        # Execute schema
        conn.executescript(schema)

        # Commit changes
        conn.commit()

        print(f"Database initialized at {db_path}")
        return True
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database()