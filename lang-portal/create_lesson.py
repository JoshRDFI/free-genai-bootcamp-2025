#!/usr/bin/env python3
"""
Interactive script for creating language lessons and generating audio files.
This script helps create lessons by prompting for lesson content and generating
the corresponding audio files using the TTS system.
"""

import json
import os
from datetime import datetime
from generate_japanese_tts import generate_tts_audio, check_tts_service, create_output_directory

LESSONS_DIR = "frontend/public/lessons"
METADATA_FILE = "frontend/public/lessons/metadata.json"

def ensure_directories():
    """Create necessary directories if they don't exist"""
    if not os.path.exists(LESSONS_DIR):
        os.makedirs(LESSONS_DIR)
        print(f"Created lessons directory: {LESSONS_DIR}")

def load_metadata():
    """Load existing lesson metadata"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"lessons": []}

def save_metadata(metadata):
    """Save lesson metadata"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def create_lesson():
    """Interactive function to create a new lesson"""
    print("\n=== Create New Lesson ===")
    
    # Get lesson details
    title = input("\nEnter lesson title: ").strip()
    while not title:
        print("Title cannot be empty!")
        title = input("Enter lesson title: ").strip()

    description = input("\nEnter lesson description: ").strip()
    
    # Get Japanese text
    print("\nEnter the Japanese text for the lesson (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if not line and lines:  # Empty line and we have content
            break
        if line:  # Non-empty line
            lines.append(line)
    
    text = "\n".join(lines)
    if not text:
        print("Error: No text provided!")
        return

    # Get voice preference
    while True:
        voice = input("\nChoose voice (male/female): ").lower().strip()
        if voice in ['male', 'female']:
            break
        print("Invalid choice! Please enter 'male' or 'female'")

    # Generate filename from title
    filename = title.lower().replace(' ', '_')
    
    # Generate audio
    print("\nGenerating audio...")
    if generate_tts_audio(text, filename, voice_id=voice):
        # Create lesson metadata
        lesson_data = {
            "id": len(load_metadata()["lessons"]) + 1,
            "title": title,
            "description": description,
            "filename": f"{filename}.mp3",
            "text": text,
            "voice": voice,
            "created_at": datetime.now().isoformat()
        }
        
        # Save metadata
        metadata = load_metadata()
        metadata["lessons"].append(lesson_data)
        save_metadata(metadata)
        
        print(f"\n✓ Lesson created successfully!")
        print(f"Audio file: {filename}.mp3")
        print(f"Metadata saved to: {METADATA_FILE}")
    else:
        print("\n✗ Failed to generate audio. Lesson not created.")

def main():
    """Main function"""
    print("Language Lesson Creator")
    print("=" * 40)
    
    # Check TTS service
    if not check_tts_service():
        return
    
    # Ensure directories exist
    ensure_directories()
    create_output_directory()
    
    while True:
        print("\nOptions:")
        print("1. Create new lesson")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == "1":
            create_lesson()
        elif choice == "2":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main() 