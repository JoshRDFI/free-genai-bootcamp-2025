import pytest
from src.validator import JLPTValidator

@pytest.fixture
def validator():
    return JLPTValidator(config_path="config/config.json")

def test_validate_level(validator):
    assert validator.validate_level("食べる", "N5") is True
    assert validator.validate_level("難しい", "N5") is False

def test_suggest_level(validator):
    assert validator.suggest_level("食べる") == "N5"
    assert validator.suggest_level("難しい") == "N4"
    assert validator.suggest_level("未知の単語") == "Unknown"