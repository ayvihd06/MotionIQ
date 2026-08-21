import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 33 MediaPipe Landmark Indices Mapping
LANDMARK_NAMES = {
    0: "nose",
    1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
    4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
    7: "left_ear", 8: "right_ear",
    9: "mouth_left", 10: "mouth_right",
    11: "left_shoulder", 12: "right_shoulder",
    13: "left_elbow", 14: "right_elbow",
    15: "left_wrist", 16: "right_wrist",
    17: "left_pinky", 18: "right_pinky",
    19: "left_index", 20: "right_index",
    21: "left_thumb", 22: "right_thumb",
    23: "left_hip", 24: "right_hip",
    25: "left_knee", 26: "right_knee",
    27: "left_ankle", 28: "right_ankle",
    29: "left_heel", 30: "right_heel",
    31: "left_foot_index", 32: "right_foot_index"
}

# Standard skeleton connections for rendering
SKELETON_CONNECTIONS = [
    # Torso
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    # Arms
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    # Left Leg
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("left_ankle", "left_heel"),
    ("left_heel", "left_foot_index"),
    ("left_ankle", "left_foot_index"),
    # Right Leg
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
    ("right_ankle", "right_heel"),
    ("right_heel", "right_foot_index"),
    ("right_ankle", "right_foot_index"),
]

@dataclass
class LandmarkPoint:
    x: float
    y: float
    z: float
    visibility: float
    presence: float = 1.0

@dataclass
class FramePose:
    frame_idx: int
    timestamp_s: float
    detected: bool
    landmarks: Dict[str, LandmarkPoint]
    raw_confidence: float

class PoseEstimator:
    """MediaPipe Pose Landmarker wrapper for frame-by-frame anatomical landmark tracking."""

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_lite.task"
        
        self.model_path = model_path
        self._landmarker = None
        # Detector is lazily initialized on first frame process to ensure instant server startup

    def _initialize_detector(self):
        if not self.model_path.exists():
            return
        
        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            output_segmentation_masks=False,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray, frame_idx: int, timestamp_s: float) -> FramePose:
        if self._landmarker is None:
            self._initialize_detector()
            if self._landmarker is None:
                return FramePose(frame_idx, timestamp_s, False, {}, 0.0)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        detection_result = self._landmarker.detect(mp_image)

        if not detection_result.pose_landmarks or len(detection_result.pose_landmarks) == 0:
            return FramePose(frame_idx, timestamp_s, False, {}, 0.0)

        landmarks_list = detection_result.pose_landmarks[0]
        mapped_landmarks: Dict[str, LandmarkPoint] = {}
        visibilities = []

        for idx, lm in enumerate(landmarks_list):
            name = LANDMARK_NAMES.get(idx, f"lm_{idx}")
            mapped_landmarks[name] = LandmarkPoint(
                x=float(lm.x),
                y=float(lm.y),
                z=float(lm.z) if hasattr(lm, "z") else 0.0,
                visibility=float(lm.visibility) if hasattr(lm, "visibility") else 0.9,
                presence=float(lm.presence) if hasattr(lm, "presence") else 1.0
            )
            visibilities.append(mapped_landmarks[name].visibility)

        avg_conf = float(np.mean(visibilities)) if visibilities else 0.0

        return FramePose(
            frame_idx=frame_idx,
            timestamp_s=timestamp_s,
            detected=True,
            landmarks=mapped_landmarks,
            raw_confidence=avg_conf
        )

    def close(self):
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

pose_estimator = PoseEstimator()
