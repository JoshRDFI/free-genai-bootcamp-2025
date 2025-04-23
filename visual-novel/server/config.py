import os
from dotenv import load_dotenv

# Load environment variables from the project's .env at startup
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '..', '.env')
load_dotenv(dotenv_path)

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, '..', 'db', 'visual_novel.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # External service endpoints
    OPEA_API_BASE_URL = os.environ.get('OPEA_API_BASE_URL', 'http://opea-api-gateway:8000')
    LLM_TEXT_URL = f"{OPEA_API_BASE_URL}/llm/text"
    TTS_URL = f"{OPEA_API_BASE_URL}/tts"
    ASR_URL = f"{OPEA_API_BASE_URL}/asr"
    LLM_VISION_URL = f"{OPEA_API_BASE_URL}/llm/vision"
    EMBEDDINGS_URL = f"{OPEA_API_BASE_URL}/embeddings"
    IMAGE_GEN_URL = f"{OPEA_API_BASE_URL}/image/generate"

    # Application
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    PORT = int(os.environ.get('PORT', 8080))
