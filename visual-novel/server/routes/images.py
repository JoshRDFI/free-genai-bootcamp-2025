# Image generation endpoints

from flask import Blueprint, request, jsonify
import requests
import os

images_bp = Blueprint('images', __name__)

@images_bp.route('/generate', methods=['POST'])
def generate_image():
    """Generate images based on prompts"""
    data = request.json
    prompt = data.get('prompt', '')
    style = data.get('style', 'anime')
    width = data.get('width', 512)
    height = data.get('height', 512)
    
    # Get the waifu-diffusion service URL
    waifu_url = os.environ.get('WAIFU_DIFFUSION_URL', 'http://localhost:9500')
    
    try:
        response = requests.post(
            f"{waifu_url}/generate",
            json={
                "prompt": prompt,
                "negative_prompt": "",
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "width": width,
                "height": height,
                "return_format": "base64"
            },
            timeout=60
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Image generation service error: {str(e)}'
        }), 500