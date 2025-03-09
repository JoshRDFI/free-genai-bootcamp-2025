# database/connection.py
import os
import sqlite3
import chromadb
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent

# Database paths from environment variables or defaults
DB_PATH = os.path.join(ROOT_DIR, os.getenv("DB_PATH", "data/db.sqlite3"))
VECTOR_DB_PATH = os.path.join(ROOT_DIR, os.getenv("VECTOR_DB_PATH", "data/vector_indices"))

# Ensure directories exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

class SQLiteConnection:
    _instance = None
    _connection = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SQLiteConnection()
        return cls._instance

    def __init__(self):
        self._connection = sqlite3.connect(DB_PATH)
        self._connection.row_factory = sqlite3.Row

        # Initialize schema if needed
        if os.getenv("DB_INITIALIZE", "false").lower() == "true":
            self._initialize_schema()

    def _initialize_schema(self):
        schema_path = os.path.join(ROOT_DIR, "database", "schema.sql")
        with open(schema_path, 'r') as f:
            schema_script = f.read()
        self._connection.executescript(schema_script)
        self._connection.commit()

    def get_connection(self):
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

class ChromaDBConnection:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ChromaDBConnection()
        return cls._instance

    def __init__(self):
        self._client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    def get_client(self):
        return self._client

    def get_or_create_collection(self, collection_name):
        return self._client.get_or_create_collection(collection_name)