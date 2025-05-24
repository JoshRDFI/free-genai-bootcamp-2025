import pytest
from src.japanese_converter import JapaneseConverter

@pytest.fixture
def converter():
    """Create a Japanese converter instance"""
    return JapaneseConverter()

def test_convert_to_romaji(converter):
    """Test conversion to romaji"""
    # Test basic hiragana
    assert converter.convert_to_romaji("こんにちは") == "konnichiha"
    
    # Test katakana
    assert converter.convert_to_romaji("コンピュータ") == "konpyu-ta"
    
    # Test mixed text
    assert converter.convert_to_romaji("日本語を勉強する") == "nihongo wo benkyou suru"
    
    # Test with punctuation
    assert converter.convert_to_romaji("こんにちは！") == "konnichiha!"

def test_convert_to_hiragana(converter):
    """Test conversion to hiragana"""
    # Test basic romaji
    assert converter.convert_to_hiragana("konnichiha") == "こんにちは"
    
    # Test with punctuation
    assert converter.convert_to_hiragana("konnichiha!") == "こんにちは！"
    
    # Test with spaces
    assert converter.convert_to_hiragana("nihongo wo benkyou suru") == "にほんごをべんきょうする"

def test_convert_to_katakana(converter):
    """Test conversion to katakana"""
    # Test basic romaji
    assert converter.convert_to_katakana("konpyu-ta") == "コンピュータ"
    
    # Test with punctuation
    assert converter.convert_to_katakana("konpyu-ta!") == "コンピュータ！"
    
    # Test with spaces
    assert converter.convert_to_katakana("nihongo wo benkyou suru") == "ニホンゴヲベンキョウスル"

def test_invalid_input(converter):
    """Test handling of invalid input"""
    # Test empty string
    assert converter.convert_to_romaji("") == ""
    assert converter.convert_to_hiragana("") == ""
    assert converter.convert_to_katakana("") == ""
    
    # Test None input
    with pytest.raises(ValueError):
        converter.convert_to_romaji(None)
    with pytest.raises(ValueError):
        converter.convert_to_hiragana(None)
    with pytest.raises(ValueError):
        converter.convert_to_katakana(None)

def test_special_characters(converter):
    """Test handling of special characters"""
    # Test with numbers
    assert converter.convert_to_romaji("123") == "123"
    assert converter.convert_to_hiragana("123") == "123"
    assert converter.convert_to_katakana("123") == "123"
    
    # Test with mixed characters
    text = "こんにちは123！"
    assert converter.convert_to_romaji(text) == "konnichiha123!"
    assert converter.convert_to_hiragana(text) == "こんにちは123！"
    assert converter.convert_to_katakana(text) == "コンニチハ123！" 