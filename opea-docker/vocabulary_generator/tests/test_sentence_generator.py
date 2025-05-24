import pytest
import asyncio
from src.sentence_generator import SentenceGenerator

@pytest.fixture
async def generator():
    """Create a sentence generator instance"""
    return SentenceGenerator()

@pytest.mark.asyncio
async def test_generate_sentence(generator):
    """Test sentence generation"""
    word = "食べる"
    level = "N5"
    
    sentence = await generator.generate_sentence(word, level)
    assert isinstance(sentence, dict)
    assert "japanese" in sentence
    assert "romaji" in sentence
    assert "english" in sentence
    assert word in sentence["japanese"]

@pytest.mark.asyncio
async def test_generate_multiple_sentences(generator):
    """Test generating multiple sentences"""
    word = "勉強する"
    level = "N5"
    count = 3
    
    sentences = await generator.generate_sentences(word, level, count)
    assert isinstance(sentences, list)
    assert len(sentences) == count
    
    for sentence in sentences:
        assert isinstance(sentence, dict)
        assert "japanese" in sentence
        assert "romaji" in sentence
        assert "english" in sentence
        assert word in sentence["japanese"]

@pytest.mark.asyncio
async def test_invalid_level(generator):
    """Test sentence generation with invalid level"""
    word = "食べる"
    level = "N6"
    
    with pytest.raises(ValueError):
        await generator.generate_sentence(word, level)

@pytest.mark.asyncio
async def test_empty_word(generator):
    """Test sentence generation with empty word"""
    word = ""
    level = "N5"
    
    with pytest.raises(ValueError):
        await generator.generate_sentence(word, level)

@pytest.mark.asyncio
async def test_sentence_validation(generator):
    """Test sentence validation"""
    word = "食べる"
    level = "N5"
    
    sentence = await generator.generate_sentence(word, level)
    
    # Validate sentence structure
    assert len(sentence["japanese"]) > 0
    assert len(sentence["romaji"]) > 0
    assert len(sentence["english"]) > 0
    
    # Validate that the target word is in the sentence
    assert word in sentence["japanese"]
    
    # Validate that the sentence is appropriate for the level
    assert generator._is_appropriate_level(sentence["japanese"], level)

@pytest.mark.asyncio
async def test_sentence_diversity(generator):
    """Test that generated sentences are diverse"""
    word = "勉強する"
    level = "N5"
    count = 5
    
    sentences = await generator.generate_sentences(word, level, count)
    
    # Check that sentences are different
    japanese_sentences = [s["japanese"] for s in sentences]
    assert len(set(japanese_sentences)) == count

@pytest.mark.asyncio
async def test_sentence_length(generator):
    """Test that generated sentences have appropriate length"""
    word = "食べる"
    level = "N5"
    
    sentence = await generator.generate_sentence(word, level)
    
    # Check that the sentence is not too short or too long
    assert 5 <= len(sentence["japanese"].split()) <= 15 