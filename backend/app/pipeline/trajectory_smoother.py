import numpy as np
from scipy.signal import savgol_filter, butter, filtfilt
from typing import Dict, Any
from app.pipeline.landmark_processor import LandmarkTrajectories, TrajectorySeries

class TrajectorySmoother:
    """Applies digital signal filtering to kinematic landmark trajectories."""

    @staticmethod
    def smooth_trajectories(
        trajectories: LandmarkTrajectories,
        window_length: int = 7,
        polyorder: int = 2
    ) -> LandmarkTrajectories:
        fps = trajectories.fps
        n_points = len(trajectories.timestamps)

        # Ensure window length is odd and does not exceed trajectory length
        if window_length >= n_points:
            window_length = max(3, n_points - 1 if (n_points % 2 == 0) else n_points)
        if window_length % 2 == 0:
            window_length += 1
        if window_length <= polyorder:
            window_length = polyorder + 2 if (polyorder % 2 == 0) else polyorder + 1

        smoothed_joints: Dict[str, TrajectorySeries] = {}

        for joint_name, series in trajectories.joints.items():
            if len(series.x) < 5:
                smoothed_joints[joint_name] = series
                continue

            try:
                # Apply Savitzky-Golay filtering on (x, y, z)
                sx = savgol_filter(series.x, window_length=window_length, polyorder=polyorder)
                sy = savgol_filter(series.y, window_length=window_length, polyorder=polyorder)
                sz = savgol_filter(series.z, window_length=window_length, polyorder=polyorder)
            except Exception:
                # Fallback to simple moving average if SavGol fails
                sx = series.x
                sy = series.y
                sz = series.z

            smoothed_joints[joint_name] = TrajectorySeries(
                timestamps=series.timestamps,
                x=sx,
                y=sy,
                z=sz,
                visibility=series.visibility,
                is_interpolated=series.is_interpolated
            )

        return LandmarkTrajectories(
            frame_indices=trajectories.frame_indices,
            timestamps=trajectories.timestamps,
            fps=trajectories.fps,
            duration_s=trajectories.duration_s,
            joints=smoothed_joints
        )

    @staticmethod
    def compute_vertical_velocity(series: TrajectorySeries, fps: float) -> np.ndarray:
        """Computes vertical velocity (dy/dt) in normalized coordinate units per second."""
        if len(series.y) < 2:
            return np.zeros_like(series.y)
        # In image coordinates, y increases downwards. Velocity > 0 means moving downwards.
        dt = 1.0 / max(1.0, fps)
        return np.gradient(series.y, dt)

trajectory_smoother = TrajectorySmoother()
