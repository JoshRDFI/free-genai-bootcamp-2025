if __name__ == "__main__":
    try:
        # Initialize the generator
        generator = AudioGenerator(tts_engine="coqui", language="ja")

        # Test segments with different speakers/roles
        test_segments = [
            {
                "text": "次の会話を聞いて、質問に答えてください。",
                "role": "announcer",
                "description": "Introduction"
            },
            {
                "text": "すみません、この電車は新宿駅に止まりますか。",
                "role": "student",
                "description": "Question"
            },
            {
                "text": "はい、止まります。各駅停車ですから、全ての駅に止まります。",
                "role": "station_staff",
                "description": "Response"
            }
        ]

        print("\n=== Starting Audio Generation Test ===")

        # Generate audio files with proper naming
        audio_files = []
        for i, segment in enumerate(test_segments, 1):
            print(f"\nProcessing segment {i}: {segment['description']}")
            print(f"Text: {segment['text']}")

            # Create output filename with role
            output_file = os.path.join(
                "audio_output",
                f"segment_{i}_{segment['role']}.wav"
            )

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Generate audio
            print(f"Generating audio for {segment['role']}...")
            audio_file = generator.generate_audio(segment['text'], output_file)

            if audio_file and os.path.exists(audio_file):
                print(f"✓ Successfully generated: {os.path.basename(audio_file)}")
                audio_files.append(audio_file)
            else:
                print(f"✗ Failed to generate audio for segment {i}")

        # Generate silence for pauses
        print("\nGenerating silence segments...")
        try:
            short_pause = generator.generate_silence(500)  # 0.5 second
            long_pause = generator.generate_silence(1000)  # 1 second
            print("✓ Successfully generated silence segments")

            # Insert pauses between segments
            final_audio_sequence = []
            for i, audio_file in enumerate(audio_files):
                final_audio_sequence.append(audio_file)
                if i < len(audio_files) - 1:
                    final_audio_sequence.append(
                        long_pause if i == 0 else short_pause
                    )
        except Exception as e:
            print(f"✗ Failed to generate silence: {str(e)}")
            final_audio_sequence = audio_files

        # Combine all audio files
        print("\nCombining audio files...")
        combined_file = os.path.join("audio_output", "combined_test_audio.wav")

        if generator.combine_audio_files(final_audio_sequence, combined_file):
            print(f"✓ Successfully combined audio: {combined_file}")

            # Print file sizes for verification
            total_size = os.path.getsize(combined_file) / 1024  # KB
            print(f"\nFile sizes:")
            print(f"Combined audio: {total_size:.2f} KB")

            # Verify the combined file exists and is not empty
            if os.path.exists(combined_file) and total_size > 0:
                print("\n=== Test Completed Successfully ===")
            else:
                print("\n=== Test Completed with Warnings ===")
                print("Warning: Combined file may be empty or invalid")
        else:
            print("✗ Failed to combine audio files")
            print("\n=== Test Failed ===")

    except Exception as e:
        print(f"\n=== Test Failed with Error ===")
        print(f"Error: {str(e)}")

    finally:
        # Clean up temporary files (optional)
        print("\nCleaning up temporary files...")
        for file in audio_files:
            try:
                if os.path.exists(file) and "segment_" in file:
                    os.remove(file)
            except Exception as e:
                print(f"Warning: Could not remove temporary file {file}: {str(e)}")