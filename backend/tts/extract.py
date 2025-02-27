from TTS.api import TTS
import os

# Define base paths
BASE_DIR = "/home/sage/free-genai-bootcamp-2025/listening-speaking/backend/tts"
MODEL_PATH = os.path.join(BASE_DIR, "tts_models--ja--kokoro--tacotron2-DDC")
VOCODER_PATH = os.path.join(BASE_DIR, "vocoder_models--ja--kokoro--hifigan_v1")
VOICES_DIR = os.path.join(BASE_DIR, "voices")

# Initialize TTS with local model paths
tts = TTS(model_path=MODEL_PATH, vocoder_path=VOCODER_PATH)

# Print model information
print("Model speakers:", tts.speakers)
print("Model languages:", tts.languages)

# Test both voices if multiple speakers are supported
if tts.speakers:
    # Test with male voice
    tts.tts_to_file(
        text="こんにちは、世界！", 
        speaker=tts.speakers[0],
        file_path=os.path.join(BASE_DIR, "output_male.wav")
    )
    
    # Test with female voice
    tts.tts_to_file(
        text="こんにちは、世界！",
        speaker=tts.speakers[1],
        file_path=os.path.join(BASE_DIR, "output_female.wav")
    )
else:
    # If no speakers available, try using reference audio directly
    try:
        # Try with male voice
        tts.tts_to_file(
            text="こんにちは、世界！",
            speaker_wav=os.path.join(VOICES_DIR, "male_voice.wav"),
            file_path=os.path.join(BASE_DIR, "output_male_ref.wav")
        )
        
        # Try with female voice
        tts.tts_to_file(
            text="こんにちは、世界！",
            speaker_wav=os.path.join(VOICES_DIR, "female_voice.wav"),
            file_path=os.path.join(BASE_DIR, "output_female_ref.wav")
        )
    except Exception as e:
        print(f"Error using reference audio: {e}")
        
        # If all else fails, generate without speaker specification
        tts.tts_to_file(
            text="こんにちは、世界！",
            file_path=os.path.join(BASE_DIR, "output_default.wav")
        )

print("Generation complete. Check the output files in the tts directory.")