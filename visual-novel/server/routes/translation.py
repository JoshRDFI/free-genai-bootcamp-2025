# Translation endpoints

from flask import Blueprint, request, jsonify
import requests
import os

translation_bp = Blueprint('translation', __name__)

@translation_bp.route('/translate', methods=['POST'])
def translate():
    """Translate text between languages"""
    data = request.json
    text = data.get('text', '')
    source_lang = data.get('source_lang', 'ja')
    target_lang = data.get('target_lang', 'en')
    
    # Get the LLM service URL
    llm_url = os.environ.get('LLM_TEXT_URL', 'http://localhost:11434')
    
    try:
        # Use the LLM service for translation
        response = requests.post(
            f"{llm_url}/api/chat",
            json={
                "model": "llama3.2",
                "messages": [
                    {
                        "role": "system", 
                        "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Provide only the translation, no explanations."
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        translated_text = result.get("message", {}).get("content", "")
        
        return jsonify({
            'status': 'success',
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Translation service error: {str(e)}'
        }), 500