import pytest
import asyncio
from datetime import datetime, timedelta
from src.reminder_system import ReminderSystem

@pytest.fixture
async def reminder_system():
    """Create a reminder system instance"""
    return ReminderSystem()

@pytest.mark.asyncio
async def test_create_reminder(reminder_system):
    """Test creating a reminder"""
    user_id = 1
    reminder_time = datetime.now() + timedelta(hours=1)
    message = "Time to study!"
    
    reminder = await reminder_system.create_reminder(user_id, reminder_time, message)
    assert reminder["user_id"] == user_id
    assert reminder["reminder_time"] == reminder_time
    assert reminder["message"] == message
    assert reminder["status"] == "pending"

@pytest.mark.asyncio
async def test_get_pending_reminders(reminder_system):
    """Test getting pending reminders"""
    user_id = 1
    now = datetime.now()
    
    # Create multiple reminders
    await reminder_system.create_reminder(user_id, now + timedelta(hours=1), "First reminder")
    await reminder_system.create_reminder(user_id, now + timedelta(hours=2), "Second reminder")
    await reminder_system.create_reminder(user_id, now + timedelta(hours=3), "Third reminder")
    
    # Get pending reminders
    reminders = await reminder_system.get_pending_reminders()
    assert len(reminders) == 3
    
    # Verify reminders are ordered by time
    for i in range(len(reminders) - 1):
        assert reminders[i]["reminder_time"] < reminders[i + 1]["reminder_time"]

@pytest.mark.asyncio
async def test_mark_reminder_sent(reminder_system):
    """Test marking a reminder as sent"""
    user_id = 1
    reminder_time = datetime.now() + timedelta(hours=1)
    
    # Create a reminder
    reminder = await reminder_system.create_reminder(user_id, reminder_time, "Test reminder")
    
    # Mark as sent
    await reminder_system.mark_reminder_sent(reminder["reminder_id"])
    
    # Verify status
    updated_reminder = await reminder_system.get_reminder(reminder["reminder_id"])
    assert updated_reminder["status"] == "sent"
    assert updated_reminder["sent_time"] is not None

@pytest.mark.asyncio
async def test_cancel_reminder(reminder_system):
    """Test canceling a reminder"""
    user_id = 1
    reminder_time = datetime.now() + timedelta(hours=1)
    
    # Create a reminder
    reminder = await reminder_system.create_reminder(user_id, reminder_time, "Test reminder")
    
    # Cancel the reminder
    await reminder_system.cancel_reminder(reminder["reminder_id"])
    
    # Verify status
    updated_reminder = await reminder_system.get_reminder(reminder["reminder_id"])
    assert updated_reminder["status"] == "canceled"

@pytest.mark.asyncio
async def test_get_user_reminders(reminder_system):
    """Test getting user's reminders"""
    user_id = 1
    now = datetime.now()
    
    # Create reminders for user
    await reminder_system.create_reminder(user_id, now + timedelta(hours=1), "First reminder")
    await reminder_system.create_reminder(user_id, now + timedelta(hours=2), "Second reminder")
    
    # Create reminder for different user
    await reminder_system.create_reminder(2, now + timedelta(hours=1), "Other user reminder")
    
    # Get user's reminders
    reminders = await reminder_system.get_user_reminders(user_id)
    assert len(reminders) == 2
    
    # Verify all reminders belong to the user
    for reminder in reminders:
        assert reminder["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_due_reminders(reminder_system):
    """Test getting due reminders"""
    user_id = 1
    now = datetime.now()
    
    # Create reminders with different times
    await reminder_system.create_reminder(user_id, now - timedelta(minutes=5), "Past reminder")
    await reminder_system.create_reminder(user_id, now + timedelta(minutes=5), "Future reminder")
    
    # Get due reminders
    due_reminders = await reminder_system.get_due_reminders()
    assert len(due_reminders) == 1
    assert due_reminders[0]["message"] == "Past reminder"

@pytest.mark.asyncio
async def test_recurring_reminder(reminder_system):
    """Test creating a recurring reminder"""
    user_id = 1
    start_time = datetime.now() + timedelta(hours=1)
    interval = timedelta(days=1)
    message = "Daily study reminder"
    
    # Create recurring reminder
    reminder = await reminder_system.create_recurring_reminder(
        user_id, start_time, interval, message
    )
    
    assert reminder["is_recurring"] == True
    assert reminder["interval"] == interval
    assert reminder["next_reminder_time"] == start_time
    
    # Mark as sent and verify next reminder is scheduled
    await reminder_system.mark_reminder_sent(reminder["reminder_id"])
    updated_reminder = await reminder_system.get_reminder(reminder["reminder_id"])
    assert updated_reminder["next_reminder_time"] == start_time + interval

@pytest.mark.asyncio
async def test_reminder_notification(reminder_system):
    """Test reminder notification handling"""
    user_id = 1
    reminder_time = datetime.now() + timedelta(minutes=5)
    
    # Create a reminder
    reminder = await reminder_system.create_reminder(user_id, reminder_time, "Test reminder")
    
    # Process notifications
    notifications = await reminder_system.process_notifications()
    assert len(notifications) > 0
    
    # Verify notification details
    notification = notifications[0]
    assert notification["user_id"] == user_id
    assert notification["message"] == "Test reminder"
    assert notification["reminder_id"] == reminder["reminder_id"] 