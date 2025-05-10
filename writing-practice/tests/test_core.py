import pytest
from pathlib import Path
import json
import yaml
from PIL import Image
import numpy as np
import os

# Import functions to test
from app import (
    load_prompts,
    load_sample_sentences,
    save_sentence,
    process_image_with_ocr,
    translate_text,
    grade_response,
    generate_sentence
)

def test_load_prompts(test_prompts):
    """Test loading prompts from YAML file"""
    prompts = load_prompts()
    assert isinstance(prompts, dict)
    assert 'translation' in prompts
    assert 'grading' in prompts
    assert 'sentence_generation' in prompts

def test_load_sample_sentences(test_sentences):
    """Test loading sample sentences"""
    sentences = load_sample_sentences()
    assert isinstance(sentences, list)
    assert len(sentences) > 0
    assert all(isinstance(s, dict) for s in sentences)
    assert all('japanese' in s for s in sentences)
    assert all('english' in s for s in sentences)

def test_save_sentence(test_dir):
    """Test saving a sentence"""
    test_sentence = {
        "japanese": "テスト文です。",
        "english": "This is a test sentence.",
        "category": "test",
        "level": "N5"
    }
    
    # Save sentence
    save_sentence(test_sentence)
    
    # Verify saved sentence
    sentences = load_sample_sentences()
    assert any(s['japanese'] == test_sentence['japanese'] for s in sentences)

def test_process_image_with_ocr(test_dir):
    """Test OCR processing"""
    # Create a test image with Japanese text
    img = Image.new('RGB', (200, 50), color='white')
    # Add some text (this is just a placeholder - real OCR would need actual text)
    img_array = np.array(img)
    img = Image.fromarray(img_array)
    
    # Save test image
    test_image_path = Path(test_dir) / "test_image.png"
    img.save(test_image_path)
    
    # Process image
    result = process_image_with_ocr(test_image_path)
    assert isinstance(result, str)
    
    # Cleanup
    test_image_path.unlink()

def test_translate_text(test_prompts):
    """Test text translation"""
    test_text = "猫が好きです。"
    result = translate_text(test_text, load_prompts())
    assert isinstance(result, str)
    assert len(result) > 0

def test_grade_response(test_prompts):
    """Test response grading"""
    target = "猫が好きです。"
    submission = "猫が好きです。"
    translation = "I like cats."
    
    result = grade_response(target, submission, translation, load_prompts())
    assert isinstance(result, str)
    assert "Grade" in result
    assert "Feedback" in result

def test_generate_sentence(test_prompts):
    """Test sentence generation"""
    word = "猫"
    category = "animals"
    
    result = generate_sentence(category, word, load_prompts())
    assert isinstance(result, dict)
    assert 'japanese' in result
    assert 'english' in result
    assert 'category' in result
    assert 'level' in result 