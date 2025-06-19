# TTS service endpoints

from flask import Blueprint, request, jsonify
import requests
import os

tts_bp = Blueprint('tts', __name__)

@tts_bp.route('/generate', methods=['POST'])
def generate_speech():
    """Generate speech from text"""
    data = request.json
    text = data.get('text', '')
    language = data.get('language', 'ja')
    voice = data.get('voice', 'female')
    
    # Get the TTS service URL
    tts_url = os.environ.get('TTS_URL', 'http://localhost:9200')
    
    try:
        response = requests.post(
            f"{tts_url}/generate",
            json={
                "text": text,
                "voice": voice,
                "language": language
            },
            timeout=30
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'TTS service error: {str(e)}'
        }), 500

@tts_bp.route('/voices', methods=['GET'])
def get_voices():
    """Get available voices"""
    tts_url = os.environ.get('TTS_URL', 'http://localhost:9200')
    
    try:
        response = requests.get(f"{tts_url}/voices", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'TTS service error: {str(e)}'
        }), 500