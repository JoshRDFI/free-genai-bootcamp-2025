import pytest
import asyncio
import streamlit as st
from src.user_interface import UserInterface

@pytest.fixture
async def ui():
    """Create a user interface instance"""
    return UserInterface()

@pytest.mark.asyncio
async def test_initialize_session_state(ui):
    """Test initializing session state"""
    await ui.initialize_session_state()
    
    assert 'user_id' in st.session_state
    assert 'current_level' in st.session_state
    assert 'study_session' in st.session_state
    assert 'preferences' in st.session_state

@pytest.mark.asyncio
async def test_render_header(ui):
    """Test rendering header"""
    header = await ui.render_header()
    assert header is not None
    assert 'title' in header
    assert 'subtitle' in header

@pytest.mark.asyncio
async def test_render_sidebar(ui):
    """Test rendering sidebar"""
    sidebar = await ui.render_sidebar()
    assert sidebar is not None
    assert 'user_info' in sidebar
    assert 'navigation' in sidebar
    assert 'settings' in sidebar

@pytest.mark.asyncio
async def test_render_dashboard(ui):
    """Test rendering dashboard"""
    # Create sample data
    progress_data = {
        'total_sessions': 10,
        'total_duration': 300,
        'total_words_reviewed': 200,
        'average_accuracy': 0.85,
        'current_streak': 5,
        'achievements': [
            {'name': 'Consistent Learner', 'progress': 100},
            {'name': 'Accuracy Master', 'progress': 75}
        ],
        'level_progress': {
            'N5': 100,
            'N4': 75,
            'N3': 50
        }
    }
    
    dashboard = await ui.render_dashboard(progress_data)
    assert dashboard is not None
    assert 'progress_summary' in dashboard
    assert 'charts' in dashboard
    assert 'achievements' in dashboard

@pytest.mark.asyncio
async def test_render_study_session(ui):
    """Test rendering study session"""
    # Create sample session data
    session_data = {
        'session_id': 1,
        'activity_type': 'typing_tutor',
        'words': [
            {
                'kanji': '食べる',
                'romaji': 'taberu',
                'english': 'to eat',
                'examples': [
                    {
                        'japanese': '私は毎日ご飯を食べます。',
                        'romaji': 'watashi wa mainichi gohan wo tabemasu.',
                        'english': 'I eat rice every day.'
                    }
                ]
            }
        ]
    }
    
    session = await ui.render_study_session(session_data)
    assert session is not None
    assert 'word_display' in session
    assert 'input_field' in session
    assert 'feedback' in session

@pytest.mark.asyncio
async def test_render_preferences(ui):
    """Test rendering preferences"""
    # Create sample preferences
    preferences = {
        'study_reminder_time': '09:00',
        'daily_goal': 50,
        'notification_enabled': True,
        'theme': 'dark',
        'language': 'en'
    }
    
    prefs_ui = await ui.render_preferences(preferences)
    assert prefs_ui is not None
    assert 'reminder_settings' in prefs_ui
    assert 'goal_settings' in prefs_ui
    assert 'appearance_settings' in prefs_ui

@pytest.mark.asyncio
async def test_render_achievements(ui):
    """Test rendering achievements"""
    # Create sample achievements
    achievements = [
        {
            'name': 'Consistent Learner',
            'description': 'Study for 7 consecutive days',
            'progress': 100,
            'completed': True
        },
        {
            'name': 'Accuracy Master',
            'description': 'Achieve 90% accuracy in a session',
            'progress': 75,
            'completed': False
        }
    ]
    
    achievements_ui = await ui.render_achievements(achievements)
    assert achievements_ui is not None
    assert 'achievement_list' in achievements_ui
    assert 'progress_bars' in achievements_ui

@pytest.mark.asyncio
async def test_render_level_progress(ui):
    """Test rendering level progress"""
    # Create sample level progress
    level_progress = {
        'N5': 100,
        'N4': 75,
        'N3': 50,
        'N2': 25,
        'N1': 0
    }
    
    progress_ui = await ui.render_level_progress(level_progress)
    assert progress_ui is not None
    assert 'level_bars' in progress_ui
    assert 'level_stats' in progress_ui

@pytest.mark.asyncio
async def test_handle_user_input(ui):
    """Test handling user input"""
    # Test valid input
    valid_input = {
        'action': 'start_session',
        'level': 'N5',
        'activity_type': 'typing_tutor'
    }
    
    result = await ui.handle_user_input(valid_input)
    assert result['success'] == True
    assert 'session_id' in result
    
    # Test invalid input
    invalid_input = {
        'action': 'start_session',
        'level': 'N6',  # Invalid level
        'activity_type': 'typing_tutor'
    }
    
    result = await ui.handle_user_input(invalid_input)
    assert result['success'] == False
    assert 'error' in result

@pytest.mark.asyncio
async def test_show_notification(ui):
    """Test showing notifications"""
    # Test success notification
    success_notification = await ui.show_notification(
        'Session completed!',
        'success'
    )
    assert success_notification is not None
    assert success_notification['type'] == 'success'
    
    # Test error notification
    error_notification = await ui.show_notification(
        'Invalid input',
        'error'
    )
    assert error_notification is not None
    assert error_notification['type'] == 'error' 