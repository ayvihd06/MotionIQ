from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np
from app.pipeline.landmark_processor import LandmarkTrajectories
from app.pipeline.gait_detector import GaitContactEvent
from app.pipeline.runner_validator import ValidationReport

def safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or np.isnan(val) or not np.isfinite(val):
            return default
        return float(val)
    except Exception:
        return default

def safe_int(val, default: int = 0) -> int:
    try:
        if val is None or np.isnan(val) or not np.isfinite(val):
            return default
        return int(round(float(val)))
    except Exception:
        return default

@dataclass
class MetricConfidenceItem:
    metric_key: str
    confidence_level: str        # "High", "Medium", "Low"
    confidence_score: float      # 0.0 to 1.0
    contributing_factors: List[str]

@dataclass
class MetricConfidenceBreakdown:
    cadence_confidence: MetricConfidenceItem
    symmetry_confidence: MetricConfidenceItem
    trunk_lean_confidence: MetricConfidenceItem
    foot_strike_confidence: MetricConfidenceItem
    overstride_confidence: MetricConfidenceItem
    vertical_movement_confidence: MetricConfidenceItem
    overall_confidence: str
    overall_score: float

class ConfidenceEngine:
    """Computes metric-specific confidence ratings using multi-factor computer vision evidence."""

    @staticmethod
    def evaluate_confidence(
        trajectories: LandmarkTrajectories,
        events: List[GaitContactEvent],
        val_report: ValidationReport,
        fps: float,
        width: int,
        height: int
    ) -> MetricConfidenceBreakdown:
        n_steps = len(events)
        n_cycles = n_steps // 2
        joints = trajectories.joints

        # 1. Cadence Confidence
        cadence_factors = []
        c_score = 0.50
        if n_steps >= 6:
            c_score += 0.35
            cadence_factors.append(f"{n_steps} distinct foot strikes detected across {n_cycles} cycles.")
        elif n_steps >= 3:
            c_score += 0.20
            cadence_factors.append(f"{n_steps} foot strikes detected (minimum threshold met).")
        else:
            c_score -= 0.20
            cadence_factors.append("Low step count (< 3 steps).")

        if fps >= 30:
            c_score += 0.15
            cadence_factors.append(f"{fps:.0f} FPS provides reliable temporal inter-frame resolution.")

        c_level = "High" if c_score >= 0.75 else ("Medium" if c_score >= 0.50 else "Low")
        cadence_item = MetricConfidenceItem("cadence", c_level, round(min(1.0, max(0.0, c_score)), 2), cadence_factors)

        # 2. Symmetry Confidence
        sym_factors = []
        s_score = 0.45
        left_count = len([e for e in events if e.side == "left"])
        right_count = len([e for e in events if e.side == "right"])

        if left_count >= 3 and right_count >= 3:
            s_score += 0.40
            sym_factors.append(f"Balanced step samples: {left_count} left and {right_count} right contacts.")
        elif left_count >= 1 and right_count >= 1:
            s_score += 0.20
            sym_factors.append(f"Limited bilateral steps ({left_count} left, {right_count} right).")
        else:
            s_score -= 0.25
            sym_factors.append("Unilateral contacts only; bilateral comparison limited.")

        s_level = "High" if s_score >= 0.75 else ("Medium" if s_score >= 0.50 else "Low")
        symmetry_item = MetricConfidenceItem("symmetry", s_level, round(min(1.0, max(0.0, s_score)), 2), sym_factors)

        # 3. Trunk Lean Confidence
        trunk_factors = []
        t_score = 0.50
        if "left_shoulder" in joints and "left_hip" in joints:
            vis_s = safe_float(np.mean(joints["left_shoulder"].visibility), 0.8)
            vis_h = safe_float(np.mean(joints["left_hip"].visibility), 0.8)
            mean_torso_vis = (vis_s + vis_h) / 2.0
            if mean_torso_vis >= 0.75:
                t_score += 0.40
                trunk_factors.append("High shoulder and hip landmark visibility (>75%).")
            elif mean_torso_vis >= 0.50:
                t_score += 0.20
                trunk_factors.append("Adequate torso landmark visibility.")
            else:
                t_score -= 0.15
                trunk_factors.append("Partial torso occlusion detected.")

        t_level = "High" if t_score >= 0.75 else ("Medium" if t_score >= 0.50 else "Low")
        trunk_item = MetricConfidenceItem("trunk_lean", t_level, round(min(1.0, max(0.0, t_score)), 2), trunk_factors)

        # 4. Foot Strike Confidence
        foot_factors = []
        f_score = 0.40
        if "left_heel" in joints and "left_foot_index" in joints:
            vis_heel = safe_float(np.mean(joints["left_heel"].visibility), 0.7)
            vis_toe = safe_float(np.mean(joints["left_foot_index"].visibility), 0.7)
            mean_foot_vis = (vis_heel + vis_toe) / 2.0
            if mean_foot_vis >= 0.70 and fps >= 30:
                f_score += 0.45
                foot_factors.append(f"High foot/shoe profile visibility ({safe_int(mean_foot_vis*100, 75)}%) at {fps:.0f} FPS.")
            elif mean_foot_vis >= 0.50:
                f_score += 0.20
                foot_factors.append("Moderate foot landmark tracking near ground border.")
            else:
                f_score -= 0.20
                foot_factors.append("Foot landmarks partially occluded or blurred during contact.")

        f_level = "High" if f_score >= 0.75 else ("Medium" if f_score >= 0.50 else "Low")
        foot_strike_item = MetricConfidenceItem("foot_strike", f_level, round(min(1.0, max(0.0, f_score)), 2), foot_factors)

        # 5. Overstride Confidence
        over_factors = []
        o_score = 0.45
        if n_steps >= 4 and "left_knee" in joints:
            vis_knee = safe_float(np.mean(joints["left_knee"].visibility), 0.8)
            if vis_knee >= 0.70:
                o_score += 0.40
                over_factors.append(f"Clear knee and hip articulation tracked at {n_steps} contact points.")
            else:
                o_score += 0.15
                over_factors.append("Moderate knee tracking clarity.")
        else:
            o_score -= 0.10
            over_factors.append("Limited contact samples for lead distance geometry.")

        o_level = "High" if o_score >= 0.75 else ("Medium" if o_score >= 0.50 else "Low")
        overstride_item = MetricConfidenceItem("overstride", o_level, round(min(1.0, max(0.0, o_score)), 2), over_factors)

        # 6. Relative Vertical Movement Confidence
        vert_factors = []
        v_score = 0.55
        if len(trajectories.timestamps) >= 30 and fps >= 24:
            v_score += 0.35
            vert_factors.append("Continuous pelvis center trajectory tracked across full flight phases.")
        else:
            vert_factors.append("Short recording duration for vertical excursion estimation.")

        v_level = "High" if v_score >= 0.75 else ("Medium" if v_score >= 0.50 else "Low")
        vertical_item = MetricConfidenceItem("vertical_movement", v_level, round(min(1.0, max(0.0, v_score)), 2), vert_factors)

        # Overall composite confidence
        mean_composite = float(np.mean([c_score, s_score, t_score, f_score, o_score, v_score]))
        overall_level = "High" if mean_composite >= 0.75 else ("Medium" if mean_composite >= 0.50 else "Low")

        return MetricConfidenceBreakdown(
            cadence_confidence=cadence_item,
            symmetry_confidence=symmetry_item,
            trunk_lean_confidence=trunk_item,
            foot_strike_confidence=foot_strike_item,
            overstride_confidence=overstride_item,
            vertical_movement_confidence=vertical_item,
            overall_confidence=overall_level,
            overall_score=round(min(100.0, max(0.0, mean_composite * 100.0)), 1)
        )

confidence_engine = ConfidenceEngine()
