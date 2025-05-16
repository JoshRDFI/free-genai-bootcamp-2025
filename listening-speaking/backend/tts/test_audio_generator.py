from audio_generator import AudioGenerator
import os

def test_audio_generation():
    # Initialize the audio generator
    generator = AudioGenerator(tts_engine="coqui", language="ja")
    
    # Test text with some potentially inappropriate content to verify guardrails
    test_text = "こんにちは、これはテストです。今日は良い天気ですね。"
    
    # Create output directory if it doesn't exist
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test male voice generation
    male_output = os.path.join(output_dir, "test_male_voice.mp3")
    print("Testing male voice generation...")
    result = generator.generate_audio_with_male_voice(test_text, male_output)
    if result:
        print(f"Successfully generated male voice audio: {result}")
    else:
        print("Failed to generate male voice audio")
    
    # Test female voice generation
    female_output = os.path.join(output_dir, "test_female_voice.mp3")
    print("\nTesting female voice generation...")
    result = generator.generate_audio_with_female_voice(test_text, female_output)
    if result:
        print(f"Successfully generated female voice audio: {result}")
    else:
        print("Failed to generate female voice audio")
    
    # Test text sanitization
    print("\nTesting text sanitization...")
    sanitized_text = generator.sanitize_text(test_text)
    print(f"Original text: {test_text}")
    print(f"Sanitized text: {sanitized_text}")

if __name__ == "__main__":
    test_audio_generation() 