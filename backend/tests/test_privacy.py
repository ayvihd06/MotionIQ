import pytest
from pathlib import Path
from app.storage import storage_manager

def test_privacy_temporary_video_lifecycle():
    dummy_video_content = b"fake video data for privacy test"
    
    # 1. Save Temporary Video
    video_id, temp_path = storage_manager.save_temp_video("runner_session.mp4", dummy_video_content)
    assert temp_path.exists()
    assert video_id in temp_path.name

    # 2. Get Video Path finds it in temp
    found_path = storage_manager.get_raw_video_path(video_id)
    assert found_path is not None
    assert found_path == temp_path

    # 3. Cleanup Temporary Video
    cleaned = storage_manager.cleanup_temp_video(video_id)
    assert cleaned is True
    assert not temp_path.exists()

    # 4. Subsequent search returns None
    assert storage_manager.get_raw_video_path(video_id) is None
