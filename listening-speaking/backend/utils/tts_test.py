if __name__ == "__main__":
    generator = AudioGenerator(tts_engine="coqui", language="ja")
    text_segments = [
        "こんにちは、これはテストです。",
        "次の会話を聞いて、質問に答えてください。",
        "この電車は新宿駅に止まりますか。",
    ]

    audio_files = []
    for i, text in enumerate(text_segments):
        output_file = f"audio_output/segment_{i + 1}.mp3"
        audio_file = generator.generate_audio(text, output_file)
        if audio_file:
            audio_files.append(audio_file)

    # Combine audio files
    combined_file = "audio_output/combined_audio.mp3"
    if generator.combine_audio_files(audio_files, combined_file):
        print(f"Combined audio saved to {combined_file}")
    else:
        print("Failed to combine audio files.")