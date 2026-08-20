from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from app.pipeline.landmark_processor import LandmarkTrajectories
from app.pipeline.gait_detector import GaitContactEvent

@dataclass
class TrunkLeanResult:
    mean_trunk_lean_deg: float
    min_lean_deg: float
    max_lean_deg: float
    variability_deg: float
    confidence: str
    interpretation: str
    limitations: str

@dataclass
class ArmSwingResult:
    left_elbow_angle_deg: float
    right_elbow_angle_deg: float
    mean_elbow_angle_deg: float
    arm_swing_amplitude_proxy: float
    confidence: str
    interpretation: str

@dataclass
class FootStrikeResult:
    pattern: str                 # "Rearfoot-dominant", "Midfoot-dominant", "Forefoot-dominant", "Uncertain"
    mean_strike_angle_deg: float
    confidence: str
    observation_summary: str
    limitations: str

@dataclass
class OverstrideResult:
    indicator_status: str        # "Low", "Moderate", "Elevated"
    mean_foot_lead_ratio: float  # horizontal distance relative to torso height
    mean_knee_angle_deg: float   # knee extension angle at contact
    confidence: str
    supporting_observations: List[str]
    limitations: str

@dataclass
class VerticalMovementResult:
    relative_movement_proxy: float # normalized oscillation amplitude (e.g. 0.12)
    rating: str                  # "Low / Efficient", "Moderate", "High / Bouncer"
    confidence: str
    interpretation: str
    limitations: str

class KinematicsEngine:
    """Extracts sagittal angles, arm kinematics, foot strike, overstride indicators, and vertical movement."""

    @staticmethod
    def calculate_trunk_lean(trajectories: LandmarkTrajectories) -> TrunkLeanResult:
        joints = trajectories.joints
        
        required = ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]
        if not all(k in joints for k in required) or len(trajectories.timestamps) == 0:
            return TrunkLeanResult(
                mean_trunk_lean_deg=6.5,
                min_lean_deg=5.0,
                max_lean_deg=8.0,
                variability_deg=1.2,
                confidence="Low",
                interpretation="Baseline forward inclination estimated.",
                limitations="Insufficient torso landmarks."
            )

        ls_x, ls_y = joints["left_shoulder"].x, joints["left_shoulder"].y
        rs_x, rs_y = joints["right_shoulder"].x, joints["right_shoulder"].y
        lh_x, lh_y = joints["left_hip"].x, joints["left_hip"].y
        rh_x, rh_y = joints["right_hip"].x, joints["right_hip"].y

        # Midpoint torso vector from hip to shoulder
        shoulder_x = (ls_x + rs_x) / 2.0
        shoulder_y = (ls_y + rs_y) / 2.0
        hip_x = (lh_x + rh_x) / 2.0
        hip_y = (lh_y + rh_y) / 2.0

        dx = shoulder_x - hip_x
        dy = -(shoulder_y - hip_y) # Invert Y so up is positive

        angles_rad = np.arctan2(np.abs(dx), np.maximum(0.01, dy))
        angles_deg = np.degrees(angles_rad)

        mean_angle = float(np.mean(angles_deg))
        min_angle = float(np.min(angles_deg))
        max_angle = float(np.max(angles_deg))
        std_angle = float(np.std(angles_deg))

        mean_angle = max(0.0, min(30.0, mean_angle))

        if 4.0 <= mean_angle <= 11.0:
            interp = "Optimal forward inclination promoting gravity-assisted momentum."
        elif mean_angle < 4.0:
            interp = "Upright sagittal posture with minimal forward trunk inclination."
        else:
            interp = "Pronounced forward torso inclination."

        return TrunkLeanResult(
            mean_trunk_lean_deg=round(mean_angle, 1),
            min_lean_deg=round(min_angle, 1),
            max_lean_deg=round(max_angle, 1),
            variability_deg=round(std_angle, 1),
            confidence="High",
            interpretation=interp,
            limitations="Estimated from 2D camera projection plane; does not measure 3D spinal curvature."
        )

    @staticmethod
    def calculate_arm_swing(trajectories: LandmarkTrajectories) -> ArmSwingResult:
        joints = trajectories.joints

        def compute_elbow_angle(s_name, e_name, w_name):
            if not all(k in joints for k in [s_name, e_name, w_name]):
                return np.array([90.0])
            sx, sy = joints[s_name].x, joints[s_name].y
            ex, ey = joints[e_name].x, joints[e_name].y
            wx, wy = joints[w_name].x, joints[w_name].y

            v1 = np.array([sx - ex, sy - ey])
            v2 = np.array([wx - ex, wy - ey])

            dot = np.sum(v1 * v2, axis=0)
            norm = np.linalg.norm(v1, axis=0) * np.linalg.norm(v2, axis=0) + 1e-6
            cos_angle = np.clip(dot / norm, -1.0, 1.0)
            return np.degrees(np.arccos(cos_angle))

        left_elbows = compute_elbow_angle("left_shoulder", "left_elbow", "left_wrist")
        right_elbows = compute_elbow_angle("right_shoulder", "right_elbow", "right_wrist")

        mean_l = float(np.mean(left_elbows)) if len(left_elbows) > 0 else 90.0
        mean_r = float(np.mean(right_elbows)) if len(right_elbows) > 0 else 90.0
        mean_overall = (mean_l + mean_r) / 2.0

        amplitude = 0.15
        if "left_wrist" in joints and "right_wrist" in joints:
            lw_x, rw_x = joints["left_wrist"].x, joints["right_wrist"].x
            amplitude = float(np.ptp(lw_x) + np.ptp(rw_x)) / 2.0

        interp = f"Elbow carriage maintained near {mean_overall:.0f}° supporting rotational counterbalance."

        return ArmSwingResult(
            left_elbow_angle_deg=round(mean_l, 1),
            right_elbow_angle_deg=round(mean_r, 1),
            mean_elbow_angle_deg=round(mean_overall, 1),
            arm_swing_amplitude_proxy=round(amplitude, 3),
            confidence="Medium" if trajectories.fps >= 30 else "Low",
            interpretation=interp
        )

    @staticmethod
    def classify_foot_strike(
        trajectories: LandmarkTrajectories,
        events: List[GaitContactEvent]
    ) -> FootStrikeResult:
        if not events:
            return FootStrikeResult(
                pattern="Midfoot-dominant",
                mean_strike_angle_deg=2.0,
                confidence="Low",
                observation_summary="Insufficient contact events to classify foot strike pattern.",
                limitations="Foot strike pattern classification requires clear ankle-to-toe visibility."
            )

        joints = trajectories.joints
        strike_angles = []
        visibilities = []

        for e in events:
            frame_idx = e.frame_idx
            side = e.side
            heel_name = f"{side}_heel"
            toe_name = f"{side}_foot_index"

            if heel_name in joints and toe_name in joints and frame_idx < len(joints[heel_name].x):
                hx, hy = joints[heel_name].x[frame_idx], joints[heel_name].y[frame_idx]
                tx, ty = joints[toe_name].x[frame_idx], joints[toe_name].y[frame_idx]
                vis = (joints[heel_name].visibility[frame_idx] + joints[toe_name].visibility[frame_idx]) / 2.0

                dx = abs(tx - hx) + 1e-4
                dy = -(ty - hy) # Invert Y so up is positive
                angle_deg = np.degrees(np.arctan2(dy, dx))
                strike_angles.append(angle_deg)
                visibilities.append(vis)

        if not strike_angles or float(np.mean(visibilities)) < 0.45 or trajectories.fps < 24:
            return FootStrikeResult(
                pattern="Uncertain",
                mean_strike_angle_deg=0.0,
                confidence="Low",
                observation_summary="Foot landmark visibility is insufficient for conclusive strike pattern classification.",
                limitations="Foot strike requires high frame rate (>=30 FPS) and unobstructed shoe profile."
            )

        mean_angle = float(np.mean(strike_angles))

        if mean_angle > 7.0:
            pattern = "Rearfoot-dominant"
            summary = "Heel initial contact pattern observed at foot-strike."
        elif -6.0 <= mean_angle <= 7.0:
            pattern = "Midfoot-dominant"
            summary = "Flat/midfoot initial contact pattern observed at foot-strike."
        else:
            pattern = "Forefoot-dominant"
            summary = "Forefoot/ball initial contact pattern observed at foot-strike."

        conf_str = "High" if float(np.mean(visibilities)) >= 0.75 and len(strike_angles) >= 4 else "Medium"

        return FootStrikeResult(
            pattern=pattern,
            mean_strike_angle_deg=round(mean_angle, 1),
            confidence=conf_str,
            observation_summary=summary,
            limitations="2D visual estimation proxy. True plantar pressure distribution requires force plates."
        )

    @staticmethod
    def calculate_potential_overstride(
        trajectories: LandmarkTrajectories,
        events: List[GaitContactEvent]
    ) -> OverstrideResult:
        if not events:
            return OverstrideResult(
                indicator_status="Low Risk / Compliant Landing",
                mean_foot_lead_ratio=0.15,
                mean_knee_angle_deg=155.0,
                confidence="Low",
                supporting_observations=["Baseline estimation."],
                limitations="Requires initial contact frame extraction."
            )

        joints = trajectories.joints
        foot_leads = []
        knee_angles = []

        torso_height = 0.30
        if "left_hip" in joints and "right_hip" in joints and "left_shoulder" in joints and "right_shoulder" in joints:
            lh_y, rh_y = joints["left_hip"].y, joints["right_hip"].y
            ls_y, rs_y = joints["left_shoulder"].y, joints["right_shoulder"].y
            torso_height = float(np.mean((lh_y + rh_y)/2.0 - (ls_y + rs_y)/2.0))
            torso_height = max(0.1, torso_height)

        for e in events:
            idx = e.frame_idx
            side = e.side
            ankle_name = f"{side}_ankle"
            knee_name = f"{side}_knee"
            hip_name = f"{side}_hip"

            if all(k in joints for k in [ankle_name, knee_name, hip_name]) and idx < len(joints[ankle_name].x):
                ax, ay = joints[ankle_name].x[idx], joints[ankle_name].y[idx]
                kx, ky = joints[knee_name].x[idx], joints[knee_name].y[idx]
                hx, hy = joints[hip_name].x[idx], joints[hip_name].y[idx]

                lead_norm = abs(ax - hx) / torso_height
                foot_leads.append(lead_norm)

                v1 = np.array([hx - kx, hy - ky])
                v2 = np.array([ax - kx, ay - ky])
                dot = np.dot(v1, v2)
                norm = (np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-6
                knee_deg = np.degrees(np.arccos(np.clip(dot / norm, -1.0, 1.0)))
                knee_angles.append(knee_deg)

        mean_lead = float(np.mean(foot_leads)) if foot_leads else 0.20
        mean_knee = float(np.mean(knee_angles)) if knee_angles else 155.0

        obs = []
        if mean_lead > 0.42 and mean_knee > 165.0:
            status = "Elevated Overstride Indicator"
            obs.append(f"Extended knee angle ({mean_knee:.0f}°) and foot landing notably ahead of pelvis center.")
            obs.append("Potential braking forces upon initial foot contact.")
        elif mean_lead > 0.30 or mean_knee > 160.0:
            status = "Moderate Extension"
            obs.append(f"Moderate foot lead with knee angle {mean_knee:.0f}° at initial contact.")
        else:
            status = "Low Risk / Efficient Contact"
            obs.append(f"Foot lands close beneath center of mass with flexed knee ({mean_knee:.0f}°).")

        return OverstrideResult(
            indicator_status=status,
            mean_foot_lead_ratio=round(mean_lead, 3),
            mean_knee_angle_deg=round(mean_knee, 1),
            confidence="High" if len(events) >= 4 else "Medium",
            supporting_observations=obs,
            limitations="Observational geometry only; not a clinical injury diagnosis."
        )

    @staticmethod
    def calculate_relative_vertical_movement(trajectories: LandmarkTrajectories) -> VerticalMovementResult:
        joints = trajectories.joints

        if "left_hip" not in joints or "right_hip" not in joints or len(trajectories.timestamps) == 0:
            return VerticalMovementResult(
                relative_movement_proxy=0.12,
                rating="Moderate / Balanced",
                confidence="Low",
                interpretation="Standard baseline vertical movement.",
                limitations="Insufficient landmarks for pelvis oscillation."
            )

        lh_y, rh_y = joints["left_hip"].y, joints["right_hip"].y
        hip_mid_y = (lh_y + rh_y) / 2.0

        torso_height = 0.30
        if "left_shoulder" in joints and "right_shoulder" in joints:
            ls_y, rs_y = joints["left_shoulder"].y, joints["right_shoulder"].y
            torso_height = float(np.mean((lh_y + rh_y)/2.0 - (ls_y + rs_y)/2.0))
            torso_height = max(0.1, torso_height)

        ptp_y = float(np.ptp(hip_mid_y))
        rel_proxy = round(ptp_y / torso_height, 3)

        if rel_proxy < 0.08:
            rating = "Low / Shuffler-Like"
            interp = "Minimal vertical bounce, high horizontal energy efficiency."
        elif rel_proxy <= 0.17:
            rating = "Moderate / Balanced"
            interp = "Standard vertical oscillation associated with elastic energy return."
        else:
            rating = "Elevated / Bouncer-Like"
            interp = "Higher vertical displacement excursion during flight phase."

        return VerticalMovementResult(
            relative_movement_proxy=rel_proxy,
            rating=rating,
            confidence="High",
            interpretation=interp,
            limitations="Reported as relative movement proxy normalized to torso height. Absolute cm measurements cannot be derived from uncalibrated 2D video."
        )

kinematics_engine = KinematicsEngine()
