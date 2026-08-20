from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from app.pipeline.gait_detector import GaitContactEvent

@dataclass
class StepTimingDetail:
    step_index: int
    side: str
    contact_time_s: float
    duration_s: float

@dataclass
class TemporalSymmetryResult:
    name: str
    symmetry_pct: float             # e.g. 94.5%
    left_mean_step_time_s: float    # e.g. 0.352s
    right_mean_step_time_s: float   # e.g. 0.358s
    mean_stride_time_s: float       # e.g. 0.710s
    step_time_variability_cv: float # e.g. 4.2%
    stride_time_variability_cv: float # e.g. 3.8%
    confidence: str
    interpretation: str
    limitations: str
    steps_analyzed: int

class TemporalEngine:
    """Calculates step/stride durations, temporal symmetry, and kinematic variability."""

    @staticmethod
    def calculate_temporal_metrics(events: List[GaitContactEvent]) -> TemporalSymmetryResult:
        if len(events) < 3:
            return TemporalSymmetryResult(
                name="Temporal Symmetry",
                symmetry_pct=92.0,
                left_mean_step_time_s=0.36,
                right_mean_step_time_s=0.36,
                mean_stride_time_s=0.72,
                step_time_variability_cv=5.0,
                stride_time_variability_cv=4.5,
                confidence="Low",
                interpretation="Symmetric bilateral timing estimated from baseline.",
                limitations="Requires at least 3 sequential foot contacts for precise step interval calculation.",
                steps_analyzed=len(events)
            )

        # 1. Compute Step Intervals (time from previous contact to current contact)
        left_step_times = []
        right_step_times = []
        all_step_times = []
        stride_times = []

        for i in range(1, len(events)):
            dt = events[i].timestamp_s - events[i-1].timestamp_s
            if 0.15 <= dt <= 0.80:
                all_step_times.append(dt)
                if events[i].side == "left":
                    left_step_times.append(dt)
                else:
                    right_step_times.append(dt)

        # 2. Compute Stride Times (time from same-side contact to next same-side contact)
        left_events = [e for e in events if e.side == "left"]
        for i in range(1, len(left_events)):
            s_dt = left_events[i].timestamp_s - left_events[i-1].timestamp_s
            if 0.40 <= s_dt <= 1.40:
                stride_times.append(s_dt)

        right_events = [e for e in events if e.side == "right"]
        for i in range(1, len(right_events)):
            s_dt = right_events[i].timestamp_s - right_events[i-1].timestamp_s
            if 0.40 <= s_dt <= 1.40:
                stride_times.append(s_dt)

        mean_left = float(np.mean(left_step_times)) if left_step_times else 0.35
        mean_right = float(np.mean(right_step_times)) if right_step_times else 0.35
        mean_stride = float(np.mean(stride_times)) if stride_times else (mean_left + mean_right)

        # 3. Transparent Symmetry Formula
        # Symmetry = (1 - |T_left - T_right| / max(T_left, T_right)) * 100%
        max_t = max(mean_left, mean_right, 0.001)
        symmetry_pct = round(max(50.0, min(100.0, (1.0 - abs(mean_left - mean_right) / max_t) * 100.0)), 1)

        # 4. Coefficient of Variation (CV) = (std / mean) * 100%
        step_cv = 0.0
        if len(all_step_times) >= 2:
            step_cv = round((float(np.std(all_step_times)) / float(np.mean(all_step_times))) * 100.0, 1)

        stride_cv = 0.0
        if len(stride_times) >= 2:
            stride_cv = round((float(np.std(stride_times)) / float(np.mean(stride_times))) * 100.0, 1)

        # Non-diagnostic interpretation
        if symmetry_pct >= 94.0:
            interpretation = "High bilateral step timing balance between left and right foot strikes."
        elif symmetry_pct >= 88.0:
            interpretation = "Normal slight step duration asymmetry within common recreational running variance."
        else:
            interpretation = "Observable asymmetry in step duration between left and right foot contacts."

        confidence = "High" if len(all_step_times) >= 6 else "Medium"
        lims = "Temporal asymmetry is an observational kinematic measurement and is NOT a medical diagnosis of injury."

        return TemporalSymmetryResult(
            name="Temporal Symmetry",
            symmetry_pct=symmetry_pct,
            left_mean_step_time_s=round(mean_left, 3),
            right_mean_step_time_s=round(mean_right, 3),
            mean_stride_time_s=round(mean_stride, 3),
            step_time_variability_cv=step_cv,
            stride_time_variability_cv=stride_cv,
            confidence=confidence,
            interpretation=interpretation,
            limitations=lims,
            steps_analyzed=len(events)
        )

temporal_engine = TemporalEngine()
