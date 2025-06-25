#!/usr/bin/env python3
"""
Test script to verify timeout handling for lesson generation
"""

import sys
import os

# Add the renpy game directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'renpy', 'game', 'python'))

try:
    from api import APIService, make_web_request
    print("Successfully imported API modules")
    
    # Test the timeout parameter
    print("\nTesting timeout parameter...")
    
    # Test a simple request with custom timeout
    try:
        response = make_web_request('GET', 'http://localhost:8001/api/health', timeout=5)
        print(f"Health check response: {response.status_code}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test lesson generation with extended timeout
    print("\nTesting lesson generation with extended timeout...")
    try:
        lesson_data = APIService.generate_lesson(
            topic="Basic Greetings",
            grammar_points=["Basic sentence structure"],
            vocabulary_focus=["greetings"],
            lesson_number=1,
            scene_setting="classroom"
        )
        print(f"Lesson generation result: {lesson_data}")
    except Exception as e:
        print(f"Lesson generation failed: {e}")
    
    print("\nTimeout test completed!")
    
except ImportError as e:
    print(f"Failed to import API modules: {e}")
    print("Make sure you're running this from the visual-novel directory")
except Exception as e:
    print(f"Test failed: {e}") 