# database/vector_store/chroma_db.py
import chromadb
import os
from pathlib import Path

class ChromaDBConnection:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls, persist_directory=None):
        if cls._instance is None:
            cls._instance = ChromaDBConnection(persist_directory)
        return cls._instance

    def __init__(self, persist_directory=None):
        if persist_directory is None:
            # Default to the vector_indices directory
            root_dir = Path(__file__).parent.parent.parent
            persist_directory = os.path.join(root_dir, "data", "vector_indices")

        os.makedirs(persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_directory)

    def get_client(self):
        return self._client

    def get_or_create_collection(self, collection_name):
        return self._client.get_or_create_collection(collection_name)