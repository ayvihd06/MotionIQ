from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
from app.pipeline.pose_estimator import FramePose

@dataclass
class ValidationReport:
    is_valid: bool
    quality_score: float
    detection_rate_pct: float
    full_body_visible: bool
    feet_visible: bool
    status: str
    reasons: List[str]
    warnings: List[str]

class RunnerValidator:
    """Validates pose presence, anatomical landmark visibility, and kinematic tracking quality."""

    @staticmethod
    def validate_tracking(
        poses: List[FramePose],
        total_frames: int,
        fps: float,
        width: int,
        height: int
    ) -> ValidationReport:
        if not poses or total_frames == 0:
            return ValidationReport(
                is_valid=False,
                quality_score=0.0,
                detection_rate_pct=0.0,
                full_body_visible=False,
                feet_visible=False,
                status="No Runner Detected",
                reasons=["No human pose landmarks detected in video."],
                warnings=["Ensure runner is clearly visible and within camera view."]
            )

        detected_poses = [p for p in poses if p.detected]
        detection_rate = len(detected_poses) / float(total_frames)
        detection_rate_pct = round(detection_rate * 100.0, 1)

        reasons = []
        warnings = []

        # 1. Runner Detection Rate Check
        if detection_rate < 0.25:
            return ValidationReport(
                is_valid=False,
                quality_score=20.0,
                detection_rate_pct=detection_rate_pct,
                full_body_visible=False,
                feet_visible=False,
                status="Insufficient Runner Tracking",
                reasons=[f"Runner detected in only {detection_rate_pct}% of frames (minimum 25% required)."],
                warnings=["Video contains excessive occlusion, motion blur, or camera framing issues."]
            )

        # 2. Lower-body and Feet Visibility Check
        ankle_vis = []
        foot_vis = []
        hip_vis = []

        for p in detected_poses:
            lms = p.landmarks
            if "left_ankle" in lms and "right_ankle" in lms:
                ankle_vis.append((lms["left_ankle"].visibility + lms["right_ankle"].visibility) / 2.0)
            if "left_foot_index" in lms and "right_foot_index" in lms:
                foot_vis.append((lms["left_foot_index"].visibility + lms["right_foot_index"].visibility) / 2.0)
            if "left_hip" in lms and "right_hip" in lms:
                hip_vis.append((lms["left_hip"].visibility + lms["right_hip"].visibility) / 2.0)

        mean_ankle_vis = float(np.mean(ankle_vis)) if ankle_vis else 0.0
        mean_foot_vis = float(np.mean(foot_vis)) if foot_vis else 0.0
        mean_hip_vis = float(np.mean(hip_vis)) if hip_vis else 0.0

        feet_visible = mean_foot_vis >= 0.50 or mean_ankle_vis >= 0.55
        full_body_visible = feet_visible and (mean_hip_vis >= 0.60)

        if not feet_visible:
            warnings.append("Feet/ankles are partially occluded or cut off near the bottom frame border.")

        # 3. Overall Biomechanical Video Quality Score (0 to 100)
        # Factors: FPS factor (30%), Resolution (20%), Detection Rate (25%), Landmark Visibility (25%)
        fps_score = min(100.0, (fps / 60.0) * 100.0)
        res_score = 100.0 if (width >= 1280 and height >= 720) else 70.0
        det_score = min(100.0, detection_rate * 100.0)
        vis_score = min(100.0, ((mean_ankle_vis + mean_hip_vis + mean_foot_vis) / 3.0) * 100.0)

        quality_score = round(
            0.30 * fps_score +
            0.20 * res_score +
            0.25 * det_score +
            0.25 * vis_score,
            1
        )

        if quality_score >= 80.0:
            status_text = "High Quality Video"
            reasons.append("High frame rate, sharp resolution, and consistent full-body tracking.")
        elif quality_score >= 55.0:
            status_text = "Acceptable Video Quality"
            reasons.append("Sufficient for running cadence, step timing, and sagittal form observation.")
        else:
            status_text = "Low Video Quality"
            reasons.append("Lower frame rate or visibility; temporal measurements may have wider confidence intervals.")

        return ValidationReport(
            is_valid=True,
            quality_score=quality_score,
            detection_rate_pct=detection_rate_pct,
            full_body_visible=full_body_visible,
            feet_visible=feet_visible,
            status=status_text,
            reasons=reasons,
            warnings=warnings
        )

runner_validator = RunnerValidator()
