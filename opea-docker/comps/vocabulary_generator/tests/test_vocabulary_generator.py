import pytest
import asyncio
from src.vocabulary_generator import VocabularyGenerator

@pytest.fixture
async def generator():
    """Create a vocabulary generator instance"""
    return VocabularyGenerator()

@pytest.mark.asyncio
async def test_generate_vocabulary(generator):
    """Test vocabulary generation"""
    word = "食べる"
    level = "N5"
    
    entry = await generator.generate_vocabulary(word, level)
    assert isinstance(entry, dict)
    assert "kanji" in entry
    assert "romaji" in entry
    assert "english" in entry
    assert "examples" in entry
    assert len(entry["examples"]) > 0

@pytest.mark.asyncio
async def test_generate_multiple_entries(generator):
    """Test generating multiple vocabulary entries"""
    words = ["食べる", "勉強する", "行く"]
    level = "N5"
    
    entries = await generator.generate_multiple_entries(words, level)
    assert isinstance(entries, list)
    assert len(entries) == len(words)
    
    for entry in entries:
        assert isinstance(entry, dict)
        assert "kanji" in entry
        assert "romaji" in entry
        assert "english" in entry
        assert "examples" in entry

@pytest.mark.asyncio
async def test_invalid_level(generator):
    """Test vocabulary generation with invalid level"""
    word = "食べる"
    level = "N6"
    
    with pytest.raises(ValueError):
        await generator.generate_vocabulary(word, level)

@pytest.mark.asyncio
async def test_empty_word(generator):
    """Test vocabulary generation with empty word"""
    word = ""
    level = "N5"
    
    with pytest.raises(ValueError):
        await generator.generate_vocabulary(word, level)

@pytest.mark.asyncio
async def test_entry_validation(generator):
    """Test vocabulary entry validation"""
    word = "食べる"
    level = "N5"
    
    entry = await generator.generate_vocabulary(word, level)
    
    # Validate entry structure
    assert len(entry["kanji"]) > 0
    assert len(entry["romaji"]) > 0
    assert len(entry["english"]) > 0
    assert len(entry["examples"]) > 0
    
    # Validate that the target word is in the entry
    assert word in entry["kanji"]
    
    # Validate that the entry is appropriate for the level
    assert generator._is_appropriate_level(entry["kanji"], level)

@pytest.mark.asyncio
async def test_example_quality(generator):
    """Test that generated examples are of good quality"""
    word = "勉強する"
    level = "N5"
    
    entry = await generator.generate_vocabulary(word, level)
    
    for example in entry["examples"]:
        assert isinstance(example, dict)
        assert "japanese" in example
        assert "romaji" in example
        assert "english" in example
        assert word in example["japanese"]
        assert len(example["japanese"]) > 0
        assert len(example["romaji"]) > 0
        assert len(example["english"]) > 0

@pytest.mark.asyncio
async def test_entry_diversity(generator):
    """Test that generated entries are diverse"""
    words = ["食べる", "勉強する", "行く"]
    level = "N5"
    
    entries = await generator.generate_multiple_entries(words, level)
    
    # Check that entries are different
    kanji_entries = [e["kanji"] for e in entries]
    assert len(set(kanji_entries)) == len(words) 