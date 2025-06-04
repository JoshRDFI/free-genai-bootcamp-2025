from typing import Optional, List
import requests
import time
from log import logger
from config import ServiceConfig

class EmbeddingService:
    def __init__(self, endpoint: str, headers: dict):
        self.endpoint = endpoint
        self.headers = headers
        self.session = requests.Session()

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for the given text."""
        try:
            logger.info("Starting embedding generation")
            
            # Prepare the request payload
            payload = {
                "input": text,
                "model": "text-embedding-3-small"
            }
            
            # Try the request with retries
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info("Sending request to embedding service")
                    response = self.session.post(
                        self.endpoint,
                        json=payload,
                        headers=self.headers,
                        timeout=ServiceConfig.get_timeout("embeddings")
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "data" in result and result["data"]:
                            embedding = result["data"][0]["embedding"]
                            logger.info("Successfully generated embedding")
                            return embedding
                        else:
                            logger.error("No embedding data in response")
                    else:
                        logger.error(f"Embedding service returned error status: {response.status_code}")
                        try:
                            error_detail = response.json()
                            logger.error(f"Response content: {error_detail}")
                        except:
                            logger.error(f"Response content: {response.text}")
                            
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise

            raise Exception("Failed to generate embedding after all retries")

        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            return None 