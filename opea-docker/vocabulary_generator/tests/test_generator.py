import pytest
from src.generator import VocabularyGenerator
import os

@pytest.fixture
def generator():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
    return VocabularyGenerator(config_path)

@pytest.mark.asyncio
async def test_generate_vocabulary_entry(generator):
    word = "食べる"
    level = "N5"
    entry = await generator.generate_vocabulary_entry(word, level)
    
    assert entry is not None
    assert 'kanji' in entry
    assert 'romaji' in entry
    assert 'english' in entry
    assert 'examples' in entry
    assert entry['kanji'] == word

@pytest.mark.asyncio
async def test_generate_examples(generator):
    word = "食べる"
    level = "N5"
    examples = await generator.sentence_gen.generate_examples(word, level)
    
    assert examples is not None
    assert len(examples) > 0
    for example in examples:
        assert 'japanese' in example
        assert 'english' in example
        assert word in example['japanese']

@pytest.mark.asyncio
async def test_validate_entry(generator):
    word = "食べる"
    level = "N5"
    entry = await generator.generate_vocabulary_entry(word, level)
    
    is_valid = generator.validator.validate_entry(entry, level)
    assert is_valid is True

@pytest.mark.asyncio
async def test_invalid_level(generator):
    word = "食べる"
    level = "N6"  # Invalid level
    with pytest.raises(ValueError):
        await generator.generate_vocabulary_entry(word, level)

def test_create_vocabulary_prompt(generator):
    prompt = generator._create_vocabulary_prompt("食べる", "N5")
    assert "食べる" in prompt
    assert "JLPT N5" in prompt