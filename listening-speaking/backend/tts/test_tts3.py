from TTS.api import TTS
import os

# Define base paths
BASE_DIR = "/home/sage/free-genai-bootcamp-2025/listening-speaking/backend/tts"
VOICES_DIR = os.path.join(BASE_DIR, "voices")

try:
    # Initialize TTS with model name instead of path
    tts = TTS("tts_models/ja/kokoro/tacotron2-DDC")
    print("Model loaded successfully!")

    # Test with male voice reference
    male_voice_path = os.path.join(VOICES_DIR, "male_voice.wav")
    if os.path.exists(male_voice_path):
        print(f"Found male voice file at: {male_voice_path}")
        output_male_path = os.path.join(BASE_DIR, "output_male_ref.wav")
        tts.tts_to_file(
            text="こんにちは、世界！",
            speaker_wav=male_voice_path,
            file_path=output_male_path
        )
        print(f"Generated male voice output at: {output_male_path}")

    # Test with female voice reference
    female_voice_path = os.path.join(VOICES_DIR, "female_voice.wav")
    if os.path.exists(female_voice_path):
        print(f"Found female voice file at: {female_voice_path}")
        output_female_path = os.path.join(BASE_DIR, "output_female_ref.wav")
        tts.tts_to_file(
            text="こんにちは、世界！",
            speaker_wav=female_voice_path,
            file_path=output_female_path
        )
        print(f"Generated female voice output at: {output_female_path}")

except Exception as e:
    print(f"Error occurred: {str(e)}")
    print("\nTrying alternative approach...")

    # Try loading with different model name format
    try:
        tts = TTS("tts_models--ja--kokoro--tacotron2-DDC")
        print("Model loaded successfully with alternative name!")
        # ... rest of the code would repeat here ...
    except Exception as e2:
        print(f"Alternative approach also failed: {str(e2)}")

print("\nScript completed.")