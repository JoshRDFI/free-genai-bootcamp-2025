import os
from TTS.api import TTS

# Define base paths
BASE_DIR = "/home/sage/free-genai-bootcamp-2025/listening-speaking/backend/tts"
MODEL_DIR = os.path.join(BASE_DIR, "tts_models--ja--kokoro--tacotron2-DDC")
VOCODER_DIR = os.path.join(BASE_DIR, "vocoder_models--ja--kokoro--hifigan_v1")
VOICES_DIR = os.path.join(BASE_DIR, "voices")

# Print available files
print("Model directory contents:")
print(os.listdir(MODEL_DIR))
print("\nVocoder directory contents:")
print(os.listdir(VOCODER_DIR))

# Try loading the model using the model name instead of path
try:
    tts = TTS("tts_models/ja/kokoro/tacotron2-DDC")
    print("\nModel loaded successfully!")
    print("Available speakers:", tts.speakers)

    # Test generation
    output_path = os.path.join(BASE_DIR, "test_output.wav")
    tts.tts_to_file(text="こんにちは、世界！", file_path=output_path)
    print(f"\nGenerated test file at: {output_path}")

except Exception as e:
    print(f"\nError loading model: {e}")