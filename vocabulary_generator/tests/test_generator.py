import pytest
from src.generator import VocabularyGenerator

@pytest.fixture
def generator():
    return VocabularyGenerator(config_path="config/config.json")

def test_create_vocabulary_prompt(generator):
    prompt = generator._create_vocabulary_prompt("食べる", "N5")
    assert "食べる" in prompt
    assert "JLPT N5" in prompt