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
    # OPEA_API_BASE_URL = os.environ.get('OPEA_API_BASE_URL', 'http://opea-api-gateway:8000') # Commented out as we connect directly
    LLM_TEXT_URL = os.environ.get('LLM_TEXT_URL', "http://llm_text:9000/llm/text")
    TTS_URL = os.environ.get('TTS_URL', "http://tts:9200/tts")
    ASR_URL = os.environ.get('ASR_URL', "http://asr:9300/asr")
    LLM_VISION_URL = os.environ.get('LLM_VISION_URL', "http://llm-vision:9100/llm/vision")
    EMBEDDINGS_URL = os.environ.get('EMBEDDINGS_URL', "http://embeddings:6000/embeddings")
    # Use the opea-docker waifu-diffusion service instead of our own
    IMAGE_GEN_URL = os.environ.get('IMAGE_GEN_URL', "http://waifu-diffusion:9500/image/generate")

    # Application
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    PORT = int(os.environ.get('PORT', 8080))
