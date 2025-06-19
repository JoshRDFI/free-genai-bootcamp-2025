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
        'sqlite:///' + os.path.join(basedir, '..', '..', 'data', 'shared_db', 'visual_novel.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # External service endpoints
    # Direct connections to opea-docker services
    OLLAMA_SERVER_URL = os.environ.get('OLLAMA_SERVER_URL', 'http://ollama-server:11434')
    LLM_TEXT_URL = os.environ.get('LLM_TEXT_URL', 'http://ollama-server:11434')
    GUARDRAILS_URL = os.environ.get('GUARDRAILS_URL', 'http://guardrails:9400')
    CHROMADB_URL = os.environ.get('CHROMADB_URL', 'http://chromadb:8000')
    TTS_URL = os.environ.get('TTS_URL', 'http://tts:9200')
    ASR_URL = os.environ.get('ASR_URL', 'http://asr:9300')
    LLM_VISION_URL = os.environ.get('LLM_VISION_URL', 'http://llm-vision:9101')
    IMAGE_GEN_URL = os.environ.get('WAIFU_DIFFUSION_URL', 'http://waifu-diffusion:9500')
    EMBEDDINGS_URL = os.environ.get('EMBEDDINGS_URL', 'http://embeddings:6000')
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://ollama-server:11434')

    # Application
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    PORT = int(os.environ.get('PORT', 8080))
