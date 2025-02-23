if __name__ == "__main__":
    asr = ASREngine(model_name="base")  # Use the "base" model for testing
    input_audio = "example_audio.mp3"  # Replace with the path to your audio file

    print("Processing audio...")
    transcript = asr.process_audio(input_audio)

    if transcript:
        print("Transcription successful!")
        print("Sanitized Transcript:")
        print(transcript)
    else:
        print("Failed to process audio.")