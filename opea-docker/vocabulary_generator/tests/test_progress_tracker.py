import pytest
import asyncio
from datetime import datetime, timedelta
from src.progress_tracker import ProgressTracker

@pytest.fixture
async def tracker():
    """Create a progress tracker instance"""
    return ProgressTracker()

@pytest.mark.asyncio
async def test_track_study_session(tracker):
    """Test tracking a study session"""
    user_id = 1
    session_data = {
        "duration": 30,
        "words_reviewed": 20,
        "correct_answers": 15,
        "jlpt_level": "N5"
    }
    
    progress = await tracker.track_study_session(user_id, session_data)
    assert progress["user_id"] == user_id
    assert progress["session_date"] == datetime.now().date()
    assert progress["total_duration"] == session_data["duration"]
    assert progress["words_reviewed"] == session_data["words_reviewed"]
    assert progress["accuracy"] == 0.75  # 15/20

@pytest.mark.asyncio
async def test_get_user_progress(tracker):
    """Test getting user progress"""
    user_id = 1
    
    # Track multiple sessions
    await tracker.track_study_session(user_id, {
        "duration": 30,
        "words_reviewed": 20,
        "correct_answers": 15,
        "jlpt_level": "N5"
    })
    
    await tracker.track_study_session(user_id, {
        "duration": 45,
        "words_reviewed": 30,
        "correct_answers": 25,
        "jlpt_level": "N5"
    })
    
    # Get progress
    progress = await tracker.get_user_progress(user_id)
    assert progress["total_sessions"] == 2
    assert progress["total_duration"] == 75
    assert progress["total_words_reviewed"] == 50
    assert progress["average_accuracy"] == 0.8  # (15+25)/(20+30)

@pytest.mark.asyncio
async def test_get_level_progress(tracker):
    """Test getting level-specific progress"""
    user_id = 1
    
    # Track sessions for different levels
    await tracker.track_study_session(user_id, {
        "duration": 30,
        "words_reviewed": 20,
        "correct_answers": 15,
        "jlpt_level": "N5"
    })
    
    await tracker.track_study_session(user_id, {
        "duration": 45,
        "words_reviewed": 30,
        "correct_answers": 25,
        "jlpt_level": "N4"
    })
    
    # Get N5 progress
    n5_progress = await tracker.get_level_progress(user_id, "N5")
    assert n5_progress["total_sessions"] == 1
    assert n5_progress["total_duration"] == 30
    assert n5_progress["total_words_reviewed"] == 20
    assert n5_progress["average_accuracy"] == 0.75

@pytest.mark.asyncio
async def test_get_daily_progress(tracker):
    """Test getting daily progress"""
    user_id = 1
    today = datetime.now().date()
    
    # Track sessions for today
    await tracker.track_study_session(user_id, {
        "duration": 30,
        "words_reviewed": 20,
        "correct_answers": 15,
        "jlpt_level": "N5"
    })
    
    await tracker.track_study_session(user_id, {
        "duration": 45,
        "words_reviewed": 30,
        "correct_answers": 25,
        "jlpt_level": "N5"
    })
    
    # Get today's progress
    daily_progress = await tracker.get_daily_progress(user_id, today)
    assert daily_progress["total_sessions"] == 2
    assert daily_progress["total_duration"] == 75
    assert daily_progress["total_words_reviewed"] == 50
    assert daily_progress["average_accuracy"] == 0.8

@pytest.mark.asyncio
async def test_get_streak(tracker):
    """Test getting study streak"""
    user_id = 1
    today = datetime.now().date()
    
    # Track sessions for consecutive days
    for i in range(5):
        date = today - timedelta(days=i)
        await tracker.track_study_session(user_id, {
            "duration": 30,
            "words_reviewed": 20,
            "correct_answers": 15,
            "jlpt_level": "N5",
            "session_date": date
        })
    
    # Get streak
    streak = await tracker.get_streak(user_id)
    assert streak["current_streak"] == 5
    assert streak["longest_streak"] == 5

@pytest.mark.asyncio
async def test_get_achievements(tracker):
    """Test getting user achievements"""
    user_id = 1
    
    # Track sessions to earn achievements
    for _ in range(10):
        await tracker.track_study_session(user_id, {
            "duration": 30,
            "words_reviewed": 20,
            "correct_answers": 18,
            "jlpt_level": "N5"
        })
    
    # Get achievements
    achievements = await tracker.get_achievements(user_id)
    assert len(achievements) > 0
    assert any(a["name"] == "Consistent Learner" for a in achievements)
    assert any(a["name"] == "Accuracy Master" for a in achievements)

@pytest.mark.asyncio
async def test_get_progress_summary(tracker):
    """Test getting progress summary"""
    user_id = 1
    
    # Track sessions
    await tracker.track_study_session(user_id, {
        "duration": 30,
        "words_reviewed": 20,
        "correct_answers": 15,
        "jlpt_level": "N5"
    })
    
    # Get summary
    summary = await tracker.get_progress_summary(user_id)
    assert "total_sessions" in summary
    assert "total_duration" in summary
    assert "total_words_reviewed" in summary
    assert "average_accuracy" in summary
    assert "current_streak" in summary
    assert "achievements" in summary
    assert "level_progress" in summary 