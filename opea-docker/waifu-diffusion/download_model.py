from huggingface_hub import snapshot_download
import os

def download_model():
    # Create the model directory if it doesn't exist
    os.makedirs("/app/data/waifu", exist_ok=True)
    
    # Download the model from Hugging Face
    model_id = "hakurei/waifu-diffusion"
    snapshot_download(
        repo_id=model_id,
        local_dir="/app/data/waifu",
        local_dir_use_symlinks=False
    )

if __name__ == "__main__":
    download_model() 