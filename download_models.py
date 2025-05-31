import os
from pathlib import Path
import sys
import logging
import getpass
import platform

# HuggingFace imports
from transformers import (
    AutoModelForCausalLM, AutoProcessor, 
    WhisperForConditionalGeneration, WhisperProcessor,
    AutoTokenizer, AutoModel, 
    LlavaForConditionalGeneration,
)
from diffusers import StableDiffusionPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configs
MODELS = [
    {
        'name': 'LLaVA',
        'repo': 'llava-hf/llava-1.5-7b-hf',
        'path': Path('data/llava_vision'),
        'download_fn': lambda repo, path: (
            AutoProcessor.from_pretrained(repo, cache_dir=path),
            LlavaForConditionalGeneration.from_pretrained(repo, cache_dir=path)
        )
    },
    {
        'name': 'XTTS V2',
        'repo': 'coqui/xtts-v2',
        'path': Path('data/tts_data/tts/tts_models--multilingual--multi-dataset--xtts_v2'),
        'download_fn': lambda repo, path: (
            AutoProcessor.from_pretrained(repo, cache_dir=path),
            AutoModelForCausalLM.from_pretrained(repo, cache_dir=path)
        )
    },
    {
        'name': 'Whisper (large-v3)',
        'repo': 'openai/whisper-large-v3',
        'path': Path('data/asr_data'),
        'download_fn': lambda repo, path: (
            WhisperProcessor.from_pretrained(repo, cache_dir=path),
            WhisperForConditionalGeneration.from_pretrained(repo, cache_dir=path)
        )
    },
    {
        'name': 'Embeddings (all-MiniLM-L6-v2)',
        'repo': 'sentence-transformers/all-MiniLM-L6-v2',
        'path': Path('data/embeddings'),
        'download_fn': lambda repo, path: (
            AutoTokenizer.from_pretrained(repo, cache_dir=path),
            AutoModel.from_pretrained(repo, cache_dir=path)
        )
    },
    {
        'name': 'Waifu Diffusion',
        'repo': 'hakurei/waifu-diffusion-v1-4',  # Changed to a compatible repo
        'path': Path('data/waifu'),
        'download_fn': lambda repo, path: (
            StableDiffusionPipeline.from_pretrained(repo, cache_dir=path)
        )
    },
]

def set_ownership(path: Path):
    """Recursively set ownership of path to the current user (if possible)."""
    if platform.system() == "Windows":
        return  # chown not supported
    try:
        import pwd
        user = getpass.getuser()
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid
        for root, dirs, files in os.walk(path):
            os.chown(root, uid, gid)
            for d in dirs:
                os.chown(os.path.join(root, d), uid, gid)
            for f in files:
                os.chown(os.path.join(root, f), uid, gid)
    except Exception as e:
        logger.warning(f"Could not set ownership for {path}: {e}")

def check_and_download(model):
    path = model['path']
    repo = model['repo']
    name = model['name']
    if not path.exists() or not any(path.iterdir()):
        logger.info(f"Downloading {name} model to {path} ...")
        path.mkdir(parents=True, exist_ok=True)
        try:
            model['download_fn'](repo, str(path))
            set_ownership(path)
            logger.info(f"{name} model downloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")
    else:
        logger.info(f"{name} model already present at {path}, skipping download.")

def main():
    logger.info("=== Model Download Script ===")
    for model in MODELS:
        check_and_download(model)
    logger.info("--- MangaOCR ---")
    logger.info("MangaOCR is installed via pip inside the Docker container. The model weights will be downloaded to the data/mangaocr_models directory on first use. If you want to pre-download, run 'python -c \"from manga_ocr import MangaOcr; MangaOcr()\"' inside the container or with the correct environment variable set.")
    logger.info("============================")

if __name__ == "__main__":
    main() 