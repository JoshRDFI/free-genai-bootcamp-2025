import pytest
import asyncio
import os
import tempfile
import json
from src.user_preferences import UserPreferencesManager

@pytest.fixture
async def preferences_manager():
    """Create a temporary preferences manager for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    prefs_path = os.path.join(temp_dir, "preferences.json")
    
    # Initialize manager
    manager = UserPreferencesManager(prefs_path)
    await manager.initialize()
    
    yield manager
    
    # Cleanup
    if os.path.exists(prefs_path):
        os.remove(prefs_path)
    os.rmdir(temp_dir)

@pytest.mark.asyncio
async def test_set_preferences(preferences_manager):
    """Test setting user preferences"""
    user_id = 1
    preferences = {
        "study_reminder_time": "09:00",
        "daily_goal": 50,
        "notification_enabled": True,
        "theme": "dark",
        "language": "en"
    }
    
    await preferences_manager.set_preferences(user_id, preferences)
    
    # Verify preferences were set
    saved_prefs = await preferences_manager.get_preferences(user_id)
    assert saved_prefs["study_reminder_time"] == preferences["study_reminder_time"]
    assert saved_prefs["daily_goal"] == preferences["daily_goal"]
    assert saved_prefs["notification_enabled"] == preferences["notification_enabled"]
    assert saved_prefs["theme"] == preferences["theme"]
    assert saved_prefs["language"] == preferences["language"]

@pytest.mark.asyncio
async def test_update_preferences(preferences_manager):
    """Test updating user preferences"""
    user_id = 1
    initial_prefs = {
        "study_reminder_time": "09:00",
        "daily_goal": 50,
        "notification_enabled": True
    }
    
    await preferences_manager.set_preferences(user_id, initial_prefs)
    
    # Update some preferences
    updates = {
        "study_reminder_time": "10:00",
        "daily_goal": 100
    }
    
    await preferences_manager.update_preferences(user_id, updates)
    
    # Verify preferences were updated
    saved_prefs = await preferences_manager.get_preferences(user_id)
    assert saved_prefs["study_reminder_time"] == updates["study_reminder_time"]
    assert saved_prefs["daily_goal"] == updates["daily_goal"]
    assert saved_prefs["notification_enabled"] == initial_prefs["notification_enabled"]

@pytest.mark.asyncio
async def test_get_default_preferences(preferences_manager):
    """Test getting default preferences"""
    user_id = 1
    prefs = await preferences_manager.get_preferences(user_id)
    
    assert "study_reminder_time" in prefs
    assert "daily_goal" in prefs
    assert "notification_enabled" in prefs
    assert "theme" in prefs
    assert "language" in prefs

@pytest.mark.asyncio
async def test_validate_preferences(preferences_manager):
    """Test preference validation"""
    user_id = 1
    invalid_prefs = {
        "study_reminder_time": "25:00",  # Invalid time
        "daily_goal": -1,  # Invalid goal
        "notification_enabled": "yes"  # Invalid boolean
    }
    
    with pytest.raises(ValueError):
        await preferences_manager.set_preferences(user_id, invalid_prefs)

@pytest.mark.asyncio
async def test_preference_persistence(preferences_manager):
    """Test that preferences persist between instances"""
    user_id = 1
    preferences = {
        "study_reminder_time": "09:00",
        "daily_goal": 50,
        "notification_enabled": True
    }
    
    await preferences_manager.set_preferences(user_id, preferences)
    
    # Create a new instance
    new_manager = UserPreferencesManager(preferences_manager.preferences_path)
    await new_manager.initialize()
    
    # Verify preferences were loaded
    saved_prefs = await new_manager.get_preferences(user_id)
    assert saved_prefs["study_reminder_time"] == preferences["study_reminder_time"]
    assert saved_prefs["daily_goal"] == preferences["daily_goal"]
    assert saved_prefs["notification_enabled"] == preferences["notification_enabled"]

@pytest.mark.asyncio
async def test_multiple_users(preferences_manager):
    """Test handling multiple users"""
    # Set preferences for user 1
    await preferences_manager.set_preferences(1, {
        "study_reminder_time": "09:00",
        "daily_goal": 50
    })
    
    # Set preferences for user 2
    await preferences_manager.set_preferences(2, {
        "study_reminder_time": "10:00",
        "daily_goal": 100
    })
    
    # Verify preferences are stored separately
    prefs1 = await preferences_manager.get_preferences(1)
    prefs2 = await preferences_manager.get_preferences(2)
    
    assert prefs1["study_reminder_time"] == "09:00"
    assert prefs2["study_reminder_time"] == "10:00"
    assert prefs1["daily_goal"] == 50
    assert prefs2["daily_goal"] == 100 