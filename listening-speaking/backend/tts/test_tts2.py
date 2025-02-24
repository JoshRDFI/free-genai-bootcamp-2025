from TTS.api import TTS
import os

# Define base paths
BASE_DIR = "/home/sage/free-genai-bootcamp-2025/listening-speaking/backend/tts"
MODEL_DIR = os.path.join(BASE_DIR, "tts_models--ja--kokoro--tacotron2-DDC")
VOCODER_DIR = os.path.join(BASE_DIR, "vocoder_models--ja--kokoro--hifigan_v1")
VOICES_DIR = os.path.join(BASE_DIR, "voices")

# Initialize TTS with local model paths
tts = TTS(model_path=MODEL_DIR, vocoder_path=VOCODER_DIR)

# Generate audio using reference audio for male voice
male_voice_path = os.path.join(VOICES_DIR, "male_voice.wav")
output_male_path = os.path.join(BASE_DIR, "output_male_ref.wav")
tts.tts_to_file(
    text="こんにちは、世界！",
    speaker_wav=male_voice_path,
    file_path=output_male_path
)
print(f"Generated male voice output: {output_male_path}")

# Generate audio using reference audio for female voice
female_voice_path = os.path.join(VOICES_DIR, "female_voice.wav")
output_female_path = os.path.join(BASE_DIR, "output_female_ref.wav")
tts.tts_to_file(
    text="こんにちは、世界！",
    speaker_wav=female_voice_path,
    file_path=output_female_path
)
print(f"Generated female voice output: {output_female_path}")