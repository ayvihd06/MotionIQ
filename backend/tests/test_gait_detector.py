import numpy as np
import pytest
from app.pipeline.landmark_processor import LandmarkTrajectories, TrajectorySeries
from app.pipeline.gait_detector import GaitEventDetector

def test_gait_event_detection_rhythm():
    fps = 30.0
    duration_s = 4.0
    n_frames = int(fps * duration_s)
    t = np.linspace(0, duration_s, n_frames)

    # 170 SPM running cadence = ~2.83 steps per second -> each foot strikes every ~0.706 seconds (~1.41 Hz per foot)
    left_y = 0.5 + 0.15 * np.sin(2 * np.pi * 1.41 * t)
    # Right foot is 180 degrees out of phase
    right_y = 0.5 + 0.15 * np.sin(2 * np.pi * 1.41 * t + np.pi)

    joints = {}
    for name in ["left_ankle", "left_heel", "left_foot_index"]:
        joints[name] = TrajectorySeries(
            timestamps=t, x=np.full_like(t, 0.4), y=left_y, z=np.zeros_like(t),
            visibility=np.full_like(t, 0.9), is_interpolated=np.zeros_like(t, dtype=bool)
        )
    for name in ["right_ankle", "right_heel", "right_foot_index"]:
        joints[name] = TrajectorySeries(
            timestamps=t, x=np.full_like(t, 0.6), y=right_y, z=np.zeros_like(t),
            visibility=np.full_like(t, 0.9), is_interpolated=np.zeros_like(t, dtype=bool)
        )

    trajectories = LandmarkTrajectories(
        frame_indices=np.arange(n_frames),
        timestamps=t,
        fps=fps,
        duration_s=duration_s,
        joints=joints
    )

    report = GaitEventDetector.detect_events(trajectories)

    assert report.total_steps >= 8
    assert 150 <= report.cadence_spm <= 190
    assert report.left_right_symmetry_pct >= 85.0
    assert len(report.events) == report.total_steps
    for e in report.events:
        assert e.confidence >= 0.5
        assert e.side in ["left", "right"]
