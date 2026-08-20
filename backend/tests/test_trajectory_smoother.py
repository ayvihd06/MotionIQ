import numpy as np
import pytest
from app.pipeline.landmark_processor import LandmarkTrajectories, TrajectorySeries
from app.pipeline.trajectory_smoother import TrajectorySmoother

def test_savgol_trajectory_smoothing():
    fps = 30.0
    t = np.linspace(0, 2.0, 60)
    # Generate noisy sine wave (simulating running vertical foot oscillation)
    clean_y = 0.5 + 0.2 * np.sin(2 * np.pi * 2.8 * t)
    noisy_y = clean_y + np.random.normal(0, 0.02, size=len(t))

    series = TrajectorySeries(
        timestamps=t,
        x=np.full_like(t, 0.5),
        y=noisy_y,
        z=np.zeros_like(t),
        visibility=np.ones_like(t),
        is_interpolated=np.zeros_like(t, dtype=bool)
    )

    trajectories = LandmarkTrajectories(
        frame_indices=np.arange(60),
        timestamps=t,
        fps=fps,
        duration_s=2.0,
        joints={"left_ankle": series}
    )

    smoothed = TrajectorySmoother.smooth_trajectories(trajectories, window_length=7, polyorder=2)
    smoothed_y = smoothed.joints["left_ankle"].y

    # Ensure smoothed trajectory variance is lower than noisy trajectory
    noisy_diff = np.mean(np.abs(np.diff(noisy_y)))
    smoothed_diff = np.mean(np.abs(np.diff(smoothed_y)))
    assert smoothed_diff < noisy_diff

def test_vertical_velocity_computation():
    fps = 30.0
    t = np.linspace(0, 1.0, 31)
    y = 0.1 * (t ** 2)  # y(t) = 0.1 * t^2 -> v(t) = 0.2 * t
    series = TrajectorySeries(
        timestamps=t,
        x=np.zeros_like(t),
        y=y,
        z=np.zeros_like(t),
        visibility=np.ones_like(t),
        is_interpolated=np.zeros_like(t, dtype=bool)
    )
    vel = TrajectorySmoother.compute_vertical_velocity(series, fps=fps)
    assert len(vel) == len(t)
    assert vel[-1] > vel[0]
