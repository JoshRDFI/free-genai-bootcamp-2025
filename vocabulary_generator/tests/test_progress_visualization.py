import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.progress_visualization import ProgressVisualization

@pytest.fixture
async def visualizer():
    """Create a progress visualization instance"""
    return ProgressVisualization()

@pytest.mark.asyncio
async def test_create_accuracy_chart(visualizer):
    """Test creating accuracy chart"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=7)
    accuracies = [0.75, 0.80, 0.85, 0.82, 0.88, 0.90, 0.92]
    data = pd.DataFrame({
        'date': dates,
        'accuracy': accuracies
    })
    
    # Create chart
    chart = await visualizer.create_accuracy_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_streak_chart(visualizer):
    """Test creating streak chart"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=30)
    study_days = [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
    data = pd.DataFrame({
        'date': dates,
        'studied': study_days
    })
    
    # Create chart
    chart = await visualizer.create_streak_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_level_progress_chart(visualizer):
    """Test creating level progress chart"""
    # Create sample data
    levels = ['N5', 'N4', 'N3', 'N2', 'N1']
    progress = [100, 75, 50, 25, 0]
    data = pd.DataFrame({
        'level': levels,
        'progress': progress
    })
    
    # Create chart
    chart = await visualizer.create_level_progress_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_word_count_chart(visualizer):
    """Test creating word count chart"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=7)
    words_learned = [20, 25, 30, 35, 40, 45, 50]
    data = pd.DataFrame({
        'date': dates,
        'words_learned': words_learned
    })
    
    # Create chart
    chart = await visualizer.create_word_count_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_study_time_chart(visualizer):
    """Test creating study time chart"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=7)
    study_times = [30, 45, 60, 45, 30, 60, 45]
    data = pd.DataFrame({
        'date': dates,
        'study_time': study_times
    })
    
    # Create chart
    chart = await visualizer.create_study_time_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_achievement_chart(visualizer):
    """Test creating achievement chart"""
    # Create sample data
    achievements = ['Consistent Learner', 'Accuracy Master', 'Speed Demon', 'Vocabulary Builder']
    progress = [100, 75, 50, 25]
    data = pd.DataFrame({
        'achievement': achievements,
        'progress': progress
    })
    
    # Create chart
    chart = await visualizer.create_achievement_chart(data)
    assert chart is not None
    assert 'data' in chart
    assert 'layout' in chart

@pytest.mark.asyncio
async def test_create_progress_dashboard(visualizer):
    """Test creating progress dashboard"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=7)
    accuracies = [0.75, 0.80, 0.85, 0.82, 0.88, 0.90, 0.92]
    words_learned = [20, 25, 30, 35, 40, 45, 50]
    study_times = [30, 45, 60, 45, 30, 60, 45]
    
    data = pd.DataFrame({
        'date': dates,
        'accuracy': accuracies,
        'words_learned': words_learned,
        'study_time': study_times
    })
    
    # Create dashboard
    dashboard = await visualizer.create_progress_dashboard(data)
    assert dashboard is not None
    assert 'accuracy_chart' in dashboard
    assert 'word_count_chart' in dashboard
    assert 'study_time_chart' in dashboard

@pytest.mark.asyncio
async def test_create_heatmap(visualizer):
    """Test creating study heatmap"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=30)
    study_times = np.random.randint(0, 120, size=30)
    data = pd.DataFrame({
        'date': dates,
        'study_time': study_times
    })
    
    # Create heatmap
    heatmap = await visualizer.create_heatmap(data)
    assert heatmap is not None
    assert 'data' in heatmap
    assert 'layout' in heatmap 