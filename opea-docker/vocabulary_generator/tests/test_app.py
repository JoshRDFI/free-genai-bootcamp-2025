import pytest
import asyncio
import streamlit as st
from app import VocabularyApp

@pytest.fixture
async def app():
    """Create a vocabulary app instance"""
    return VocabularyApp()

@pytest.mark.asyncio
async def test_app_initialization(app):
    """Test app initialization"""
    await app.initialize()
    
    assert app.db is not None
    assert app.ui is not None
    assert app.scheduler is not None
    assert app.reminder_system is not None
    assert app.progress_tracker is not None

@pytest.mark.asyncio
async def test_user_registration(app):
    """Test user registration"""
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    }
    
    user = await app.register_user(user_data)
    assert user['user_id'] is not None
    assert user['name'] == user_data['name']
    assert user['email'] == user_data['email']
    assert user['current_level'] == user_data['current_level']

@pytest.mark.asyncio
async def test_user_login(app):
    """Test user login"""
    # First register a user
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    }
    user = await app.register_user(user_data)
    
    # Test login
    logged_in_user = await app.login_user(user['email'])
    assert logged_in_user['user_id'] == user['user_id']
    assert logged_in_user['name'] == user['name']

@pytest.mark.asyncio
async def test_study_session_flow(app):
    """Test complete study session flow"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Start session
    session = await app.start_study_session(user['user_id'], 'N5', 'typing_tutor')
    assert session['session_id'] is not None
    assert session['status'] == 'active'
    
    # Get session words
    words = await app.get_session_words(session['session_id'])
    assert len(words) > 0
    
    # Submit answer
    result = await app.submit_answer(session['session_id'], words[0]['word_id'], 'taberu')
    assert result['correct'] is not None
    assert result['feedback'] is not None
    
    # End session
    completed_session = await app.end_study_session(session['session_id'])
    assert completed_session['status'] == 'completed'
    assert completed_session['end_time'] is not None

@pytest.mark.asyncio
async def test_progress_tracking(app):
    """Test progress tracking"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Complete a study session
    session = await app.start_study_session(user['user_id'], 'N5', 'typing_tutor')
    words = await app.get_session_words(session['session_id'])
    for word in words:
        await app.submit_answer(session['session_id'], word['word_id'], 'taberu')
    await app.end_study_session(session['session_id'])
    
    # Get progress
    progress = await app.get_user_progress(user['user_id'])
    assert progress['total_sessions'] > 0
    assert progress['total_duration'] > 0
    assert progress['total_words_reviewed'] > 0

@pytest.mark.asyncio
async def test_reminder_system(app):
    """Test reminder system"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Set reminder
    reminder = await app.set_study_reminder(user['user_id'], '09:00')
    assert reminder['reminder_id'] is not None
    assert reminder['status'] == 'pending'
    
    # Get user reminders
    reminders = await app.get_user_reminders(user['user_id'])
    assert len(reminders) > 0
    assert reminders[0]['reminder_id'] == reminder['reminder_id']

@pytest.mark.asyncio
async def test_preferences_management(app):
    """Test preferences management"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Set preferences
    preferences = {
        'study_reminder_time': '09:00',
        'daily_goal': 50,
        'notification_enabled': True,
        'theme': 'dark',
        'language': 'en'
    }
    
    await app.set_user_preferences(user['user_id'], preferences)
    
    # Get preferences
    saved_preferences = await app.get_user_preferences(user['user_id'])
    assert saved_preferences['study_reminder_time'] == preferences['study_reminder_time']
    assert saved_preferences['daily_goal'] == preferences['daily_goal']
    assert saved_preferences['notification_enabled'] == preferences['notification_enabled']

@pytest.mark.asyncio
async def test_achievement_system(app):
    """Test achievement system"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Complete multiple sessions to earn achievements
    for _ in range(7):
        session = await app.start_study_session(user['user_id'], 'N5', 'typing_tutor')
        words = await app.get_session_words(session['session_id'])
        for word in words:
            await app.submit_answer(session['session_id'], word['word_id'], 'taberu')
        await app.end_study_session(session['session_id'])
    
    # Get achievements
    achievements = await app.get_user_achievements(user['user_id'])
    assert len(achievements) > 0
    assert any(a['name'] == 'Consistent Learner' for a in achievements)

@pytest.mark.asyncio
async def test_level_progression(app):
    """Test level progression"""
    # Register user
    user = await app.register_user({
        'name': 'Test User',
        'email': 'test@example.com',
        'current_level': 'N5'
    })
    
    # Complete sessions with high accuracy
    for _ in range(10):
        session = await app.start_study_session(user['user_id'], 'N5', 'typing_tutor')
        words = await app.get_session_words(session['session_id'])
        for word in words:
            await app.submit_answer(session['session_id'], word['word_id'], 'taberu')
        await app.end_study_session(session['session_id'])
    
    # Check progression
    progression = await app.check_level_progression(user['user_id'])
    assert progression['can_advance'] == True
    assert progression['current_level'] == 'N5'
    assert progression['next_level'] == 'N4'
    
    # Advance level
    new_level = await app.advance_user_level(user['user_id'])
    assert new_level == 'N4' 