import requests
import base64
import os

def test_tts():
    # TTS service endpoint
    url = "http://localhost:9200/tts"
    
    # Test request payload
    payload = {
        "text": "Hello! This is a test of the text to speech service.",
        "language": "en",
        "speed": 1.0
    }
    
    try:
        # Send POST request to TTS service
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Get the response data
        data = response.json()
        
        # Decode the base64 audio data
        audio_data = base64.b64decode(data["audio"])
        
        # Save the audio file
        output_file = "test_output.wav"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        print(f"Success! Audio saved to {output_file}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return False
    except Exception as e:
        print(f"Error processing response: {e}")
        return False

if __name__ == "__main__":
    test_tts() 