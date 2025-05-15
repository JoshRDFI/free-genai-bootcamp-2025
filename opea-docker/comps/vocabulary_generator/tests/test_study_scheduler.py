import pytest
import asyncio
from datetime import datetime, timedelta
from src.study_scheduler import StudyScheduler

@pytest.fixture
async def scheduler():
    """Create a study scheduler instance"""
    return StudyScheduler()

@pytest.mark.asyncio
async def test_schedule_session(scheduler):
    """Test scheduling a study session"""
    user_id = 1
    session_time = datetime.now() + timedelta(hours=1)
    duration = 30  # minutes
    
    session = await scheduler.schedule_session(user_id, session_time, duration)
    assert session["user_id"] == user_id
    assert session["scheduled_time"] == session_time
    assert session["duration"] == duration
    assert session["status"] == "scheduled"

@pytest.mark.asyncio
async def test_get_upcoming_sessions(scheduler):
    """Test getting upcoming sessions"""
    user_id = 1
    now = datetime.now()
    
    # Schedule multiple sessions
    await scheduler.schedule_session(user_id, now + timedelta(hours=1), 30)
    await scheduler.schedule_session(user_id, now + timedelta(hours=2), 45)
    await scheduler.schedule_session(user_id, now + timedelta(hours=3), 60)
    
    # Get upcoming sessions
    sessions = await scheduler.get_upcoming_sessions(user_id)
    assert len(sessions) == 3
    
    # Verify sessions are ordered by time
    for i in range(len(sessions) - 1):
        assert sessions[i]["scheduled_time"] < sessions[i + 1]["scheduled_time"]

@pytest.mark.asyncio
async def test_cancel_session(scheduler):
    """Test canceling a study session"""
    user_id = 1
    session_time = datetime.now() + timedelta(hours=1)
    
    # Schedule a session
    session = await scheduler.schedule_session(user_id, session_time, 30)
    
    # Cancel the session
    await scheduler.cancel_session(session["session_id"])
    
    # Verify session was canceled
    updated_session = await scheduler.get_session(session["session_id"])
    assert updated_session["status"] == "canceled"

@pytest.mark.asyncio
async def test_reschedule_session(scheduler):
    """Test rescheduling a study session"""
    user_id = 1
    original_time = datetime.now() + timedelta(hours=1)
    new_time = original_time + timedelta(hours=1)
    
    # Schedule a session
    session = await scheduler.schedule_session(user_id, original_time, 30)
    
    # Reschedule the session
    updated_session = await scheduler.reschedule_session(session["session_id"], new_time)
    assert updated_session["scheduled_time"] == new_time
    assert updated_session["status"] == "scheduled"

@pytest.mark.asyncio
async def test_get_daily_schedule(scheduler):
    """Test getting daily schedule"""
    user_id = 1
    today = datetime.now().date()
    
    # Schedule sessions for today
    await scheduler.schedule_session(user_id, datetime.combine(today, datetime.min.time()) + timedelta(hours=9), 30)
    await scheduler.schedule_session(user_id, datetime.combine(today, datetime.min.time()) + timedelta(hours=14), 45)
    await scheduler.schedule_session(user_id, datetime.combine(today, datetime.min.time()) + timedelta(hours=19), 60)
    
    # Get today's schedule
    schedule = await scheduler.get_daily_schedule(user_id, today)
    assert len(schedule) == 3
    
    # Verify all sessions are on the same day
    for session in schedule:
        assert session["scheduled_time"].date() == today

@pytest.mark.asyncio
async def test_session_conflicts(scheduler):
    """Test handling of session conflicts"""
    user_id = 1
    base_time = datetime.now() + timedelta(hours=1)
    
    # Schedule first session
    await scheduler.schedule_session(user_id, base_time, 60)
    
    # Try to schedule overlapping session
    with pytest.raises(ValueError):
        await scheduler.schedule_session(user_id, base_time + timedelta(minutes=30), 60)

@pytest.mark.asyncio
async def test_session_reminders(scheduler):
    """Test session reminder functionality"""
    user_id = 1
    session_time = datetime.now() + timedelta(minutes=5)
    
    # Schedule a session with reminder
    session = await scheduler.schedule_session(user_id, session_time, 30, reminder=True)
    
    # Get pending reminders
    reminders = await scheduler.get_pending_reminders()
    assert len(reminders) > 0
    
    # Verify reminder details
    reminder = reminders[0]
    assert reminder["session_id"] == session["session_id"]
    assert reminder["user_id"] == user_id
    assert reminder["reminder_time"] < session_time

@pytest.mark.asyncio
async def test_session_completion(scheduler):
    """Test session completion tracking"""
    user_id = 1
    session_time = datetime.now() + timedelta(hours=1)
    
    # Schedule and complete a session
    session = await scheduler.schedule_session(user_id, session_time, 30)
    completed_session = await scheduler.complete_session(session["session_id"])
    
    assert completed_session["status"] == "completed"
    assert completed_session["completion_time"] is not None
    assert completed_session["actual_duration"] is not None 