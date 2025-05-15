import pytest
from src.jlpt_validator import JLPTValidator

@pytest.fixture
def validator():
    """Create a JLPT validator instance"""
    return JLPTValidator()

def test_valid_jlpt_levels(validator):
    """Test valid JLPT level validation"""
    assert validator.is_valid_level("N5")
    assert validator.is_valid_level("N4")
    assert validator.is_valid_level("N3")
    assert validator.is_valid_level("N2")
    assert validator.is_valid_level("N1")

def test_invalid_jlpt_levels(validator):
    """Test invalid JLPT level validation"""
    assert not validator.is_valid_level("N6")
    assert not validator.is_valid_level("N0")
    assert not validator.is_valid_level("N")
    assert not validator.is_valid_level("5")
    assert not validator.is_valid_level("")

def test_level_comparison(validator):
    """Test JLPT level comparison"""
    assert validator.is_higher_level("N1", "N2")
    assert validator.is_higher_level("N2", "N3")
    assert validator.is_higher_level("N3", "N4")
    assert validator.is_higher_level("N4", "N5")
    
    assert not validator.is_higher_level("N5", "N4")
    assert not validator.is_higher_level("N4", "N3")
    assert not validator.is_higher_level("N3", "N2")
    assert not validator.is_higher_level("N2", "N1")
    
    assert not validator.is_higher_level("N1", "N1")
    assert not validator.is_higher_level("N5", "N5")

def test_get_next_level(validator):
    """Test getting next JLPT level"""
    assert validator.get_next_level("N5") == "N4"
    assert validator.get_next_level("N4") == "N3"
    assert validator.get_next_level("N3") == "N2"
    assert validator.get_next_level("N2") == "N1"
    
    with pytest.raises(ValueError):
        validator.get_next_level("N1")
    
    with pytest.raises(ValueError):
        validator.get_next_level("N6")

def test_get_level_number(validator):
    """Test getting JLPT level number"""
    assert validator.get_level_number("N5") == 5
    assert validator.get_level_number("N4") == 4
    assert validator.get_level_number("N3") == 3
    assert validator.get_level_number("N2") == 2
    assert validator.get_level_number("N1") == 1
    
    with pytest.raises(ValueError):
        validator.get_level_number("N6")
    
    with pytest.raises(ValueError):
        validator.get_level_number("invalid")

def test_level_requirements(validator):
    """Test JLPT level requirements"""
    requirements = validator.get_level_requirements("N5")
    assert "vocabulary" in requirements
    assert "grammar" in requirements
    assert "kanji" in requirements
    assert "listening" in requirements
    assert "reading" in requirements
    
    with pytest.raises(ValueError):
        validator.get_level_requirements("N6") 