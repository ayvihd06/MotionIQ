import cv2
import numpy as np
import pytest
from pathlib import Path
from app.pipeline.video_loader import video_loader
from app.pipeline.pose_estimator import pose_estimator
from app.pipeline.landmark_processor import landmark_processor
from app.pipeline.trajectory_smoother import trajectory_smoother
from app.pipeline.gait_detector import gait_event_detector
from app.pipeline.video_annotator import video_annotator
from app.storage import storage_manager

@pytest.fixture
def sample_test_video(tmp_path):
    video_path = tmp_path / "synthetic_run.mp4"
    fps = 30.0
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    # Generate 30 frames of synthetic runner dot movement
    for i in range(30):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw moving torso & head
        cx = int(100 + i * 4)
        cy = int(120 + 10 * np.sin(i * 0.4))
        cv2.circle(frame, (cx, cy - 40), 12, (200, 200, 200), -1) # Head
        cv2.line(frame, (cx, cy - 30), (cx, cy + 20), (200, 200, 200), 4) # Torso
        out.write(frame)

    out.release()
    return video_path

def test_storage_manager_annotated_paths():
    p = storage_manager.get_annotated_video_path("test-123")
    assert p.name == "test-123.mp4"
    r = storage_manager.get_report_path("test-123")
    assert r.name == "test-123.pdf"

def test_video_loader_metadata(sample_test_video):
    meta = video_loader.get_metadata(sample_test_video)
    assert meta["fps"] == 30.0
    assert meta["frame_count"] == 30
    assert meta["width"] == 320
    assert meta["height"] == 240

def test_video_annotator_output(sample_test_video, tmp_path):
    output_path = tmp_path / "annotated_out.mp4"
    poses = []
    for f_idx, t_sec, frame in video_loader.stream_frames(sample_test_video):
        poses.append(pose_estimator.process_frame(frame, f_idx, t_sec))

    video_annotator.render_annotated_video(
        input_video_path=sample_test_video,
        output_video_path=output_path,
        poses=poses,
        events=[],
        fps=30.0,
        cadence_spm=165.0
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0
