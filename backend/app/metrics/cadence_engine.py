from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from app.pipeline.gait_detector import GaitContactEvent

@dataclass
class CadenceResult:
    name: str
    value: float              # Cadence in SPM
    unit: str
    confidence: str           # "High", "Medium", "Low"
    status: str               # "Estimated", "Optimal", "Normal"
    step_count: int
    cycles_used: int
    duration_s: float
    description: str
    limitations: str

class CadenceEngine:
    """Calculates running cadence from detected initial contact steps."""

    @staticmethod
    def calculate_cadence(events: List[GaitContactEvent], duration_s: float) -> CadenceResult:
        step_count = len(events)
        duration_min = max(0.01, duration_s / 60.0)

        if step_count < 2 or duration_s < 0.5:
            return CadenceResult(
                name="Cadence",
                value=165.0,
                unit="SPM",
                confidence="Low",
                status="Estimated",
                step_count=step_count,
                cycles_used=max(0, step_count // 2),
                duration_s=duration_s,
                description="Insufficient gait steps detected to compute high-confidence cadence.",
                limitations="Requires at least 2 full steps across a stable recording."
            )

        # Method 1: Total steps divided by total duration in minutes
        gross_cadence = step_count / duration_min

        # Method 2: Inter-step intervals
        intervals = [
            events[i].timestamp_s - events[i-1].timestamp_s
            for i in range(1, len(events))
            if 0.15 <= (events[i].timestamp_s - events[i-1].timestamp_s) <= 0.80
        ]

        if intervals:
            median_step_time = float(np.median(intervals))
            instantaneous_cadence = 60.0 / median_step_time
            # Weighted blend between interval-based and gross cadence
            cadence_spm = round(0.70 * instantaneous_cadence + 0.30 * gross_cadence, 1)
        else:
            cadence_spm = round(gross_cadence, 1)

        # Clamp to physiological running range
        cadence_spm = max(120.0, min(240.0, cadence_spm))
        cycles_used = step_count // 2

        confidence = "High" if step_count >= 6 else ("Medium" if step_count >= 3 else "Low")
        
        # Non-dogmatic descriptive status
        if 165.0 <= cadence_spm <= 185.0:
            status_str = "Optimal Rhythm"
        elif cadence_spm > 185.0:
            status_str = "High Step Frequency"
        else:
            status_str = "Moderate Rhythm"

        desc = f"Calculated step frequency of {cadence_spm:.0f} SPM across {step_count} detected foot contacts."
        lims = "Monocular video step detection depends on foot visibility. Does not enforce an arbitrary 180 SPM target."

        return CadenceResult(
            name="Cadence",
            value=cadence_spm,
            unit="SPM",
            confidence=confidence,
            status=status_str,
            step_count=step_count,
            cycles_used=cycles_used,
            duration_s=round(duration_s, 2),
            description=desc,
            limitations=lims
        )

cadence_engine = CadenceEngine()
