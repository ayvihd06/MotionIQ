import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.pipeline.pose_estimator import FramePose, LANDMARK_NAMES

@dataclass
class TrajectorySeries:
    timestamps: np.ndarray        # shape: (N,)
    x: np.ndarray                 # shape: (N,)
    y: np.ndarray                 # shape: (N,)
    z: np.ndarray                 # shape: (N,)
    visibility: np.ndarray        # shape: (N,)
    is_interpolated: np.ndarray   # shape: (N,) bool

@dataclass
class LandmarkTrajectories:
    frame_indices: np.ndarray
    timestamps: np.ndarray
    fps: float
    duration_s: float
    joints: Dict[str, TrajectorySeries]

class LandmarkProcessor:
    """Extracts, formats, and interpolates structured time-series trajectories for all anatomical landmarks."""

    @staticmethod
    def process_trajectories(poses: List[FramePose], fps: float) -> LandmarkTrajectories:
        if not poses:
            raise ValueError("Cannot process empty pose sequence.")

        n_frames = len(poses)
        frame_indices = np.array([p.frame_idx for p in poses], dtype=int)
        timestamps = np.array([p.timestamp_s for p in poses], dtype=float)
        duration_s = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0

        joints: Dict[str, TrajectorySeries] = {}

        # Initialize arrays for each landmark
        for idx, name in LANDMARK_NAMES.items():
            x_arr = np.full(n_frames, np.nan, dtype=float)
            y_arr = np.full(n_frames, np.nan, dtype=float)
            z_arr = np.full(n_frames, np.nan, dtype=float)
            vis_arr = np.zeros(n_frames, dtype=float)
            interp_mask = np.zeros(n_frames, dtype=bool)

            for i, p in enumerate(poses):
                if p.detected and name in p.landmarks:
                    lm = p.landmarks[name]
                    x_arr[i] = lm.x
                    y_arr[i] = lm.y
                    z_arr[i] = lm.z
                    vis_arr[i] = lm.visibility

            # Perform short-gap linear interpolation (max gap = 5 frames)
            x_clean, mask_x = LandmarkProcessor._interpolate_nans(x_arr, max_gap=5)
            y_clean, mask_y = LandmarkProcessor._interpolate_nans(y_arr, max_gap=5)
            z_clean, _ = LandmarkProcessor._interpolate_nans(z_arr, max_gap=5)
            interp_mask = mask_x | mask_y

            joints[name] = TrajectorySeries(
                timestamps=timestamps,
                x=x_clean,
                y=y_clean,
                z=z_clean,
                visibility=vis_arr,
                is_interpolated=interp_mask
            )

        return LandmarkTrajectories(
            frame_indices=frame_indices,
            timestamps=timestamps,
            fps=fps,
            duration_s=duration_s,
            joints=joints
        )

    @staticmethod
    def _interpolate_nans(arr: np.ndarray, max_gap: int = 5) -> (np.ndarray, np.ndarray):
        """Linearly interpolates short missing gaps of NaNs without extrapolating outside valid range."""
        result = arr.copy()
        n = len(arr)
        interpolated_mask = np.zeros(n, dtype=bool)

        valid_indices = np.where(~np.isnan(arr))[0]
        if len(valid_indices) == 0:
            return np.nan_to_num(result, nan=0.5), interpolated_mask
        if len(valid_indices) == 1:
            result[:] = arr[valid_indices[0]]
            return result, interpolated_mask

        for i in range(len(valid_indices) - 1):
            start_idx = valid_indices[i]
            end_idx = valid_indices[i + 1]
            gap = end_idx - start_idx - 1

            if 1 <= gap <= max_gap:
                # Interpolate
                val_start = arr[start_idx]
                val_end = arr[end_idx]
                for j in range(1, gap + 1):
                    alpha = j / (gap + 1.0)
                    idx = start_idx + j
                    result[idx] = val_start + alpha * (val_end - val_start)
                    interpolated_mask[idx] = True

        # Forward/Backward fill remaining isolated edge NaNs
        first_valid = valid_indices[0]
        last_valid = valid_indices[-1]
        result[:first_valid] = arr[first_valid]
        result[last_valid + 1:] = arr[last_valid]

        return result, interpolated_mask

landmark_processor = LandmarkProcessor()
