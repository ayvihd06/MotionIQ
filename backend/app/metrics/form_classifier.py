from dataclasses import dataclass
from typing import List, Dict, Any
from app.metrics.cadence_engine import CadenceResult
from app.metrics.temporal_engine import TemporalSymmetryResult
from app.metrics.kinematics_engine import (
    TrunkLeanResult, ArmSwingResult, FootStrikeResult, OverstrideResult, VerticalMovementResult
)

@dataclass
class FormPatternObservation:
    label: str
    category: str
    reason: str
    supporting_metrics: List[str]
    confidence: str
    scientific_note: str

class FormClassifier:
    """Transparent, explainable rule engine for observable running-form classification."""

    @staticmethod
    def classify_form_patterns(
        cadence: CadenceResult,
        temporal: TemporalSymmetryResult,
        trunk: TrunkLeanResult,
        arms: ArmSwingResult,
        foot_strike: FootStrikeResult,
        overstride: OverstrideResult,
        vertical: VerticalMovementResult
    ) -> List[FormPatternObservation]:
        observations: List[FormPatternObservation] = []

        # 1. Posture & Trunk Inclination Rules
        if trunk.mean_trunk_lean_deg < 4.0:
            observations.append(FormPatternObservation(
                label="Upright Posture Pattern",
                category="Posture",
                reason=f"Trunk forward inclination ({trunk.mean_trunk_lean_deg:.1f}°) is close to vertical (under 4°).",
                supporting_metrics=[f"Trunk lean: {trunk.mean_trunk_lean_deg:.1f}°", f"Lean range: {trunk.min_lean_deg}°–{trunk.max_lean_deg}°"],
                confidence=trunk.confidence,
                scientific_note="A slight forward lean from the ankles (5–10°) helps align the center of gravity with forward momentum."
            ))
        elif 4.0 <= trunk.mean_trunk_lean_deg <= 11.0:
            observations.append(FormPatternObservation(
                label="Forward-Leaning Dynamic Stride",
                category="Posture",
                reason=f"Trunk forward inclination ({trunk.mean_trunk_lean_deg:.1f}°) falls within the typical 4–11° gravity-assist range.",
                supporting_metrics=[f"Trunk lean: {trunk.mean_trunk_lean_deg:.1f}°"],
                confidence="High",
                scientific_note="Moderate full-body forward lean engages posterior chain muscles effectively."
            ))
        else:
            observations.append(FormPatternObservation(
                label="Pronounced Forward Lean Pattern",
                category="Posture",
                reason=f"Trunk inclination ({trunk.mean_trunk_lean_deg:.1f}°) exceeds 11°.",
                supporting_metrics=[f"Trunk lean: {trunk.mean_trunk_lean_deg:.1f}°"],
                confidence=trunk.confidence,
                scientific_note="Excessive forward lean may increase lower back muscular demand over long distances."
            ))

        # 2. Cadence & Step Rhythm Rules
        if cadence.value >= 175.0 and vertical.relative_movement_proxy < 0.09:
            observations.append(FormPatternObservation(
                label="Shuffler-Like Stride Pattern",
                category="Stride Mechanics",
                reason=f"High step cadence ({cadence.value:.0f} SPM) paired with low vertical movement proxy ({vertical.relative_movement_proxy}).",
                supporting_metrics=[f"Cadence: {cadence.value:.0f} SPM", f"Vertical proxy: {vertical.relative_movement_proxy}"],
                confidence="High",
                scientific_note="Shuffling stride patterns minimize vertical oscillation and reduce energy expenditure per step."
            ))
        elif cadence.value < 160.0 and vertical.relative_movement_proxy > 0.16:
            observations.append(FormPatternObservation(
                label="Bouncer-Like Stride Pattern",
                category="Stride Mechanics",
                reason=f"Lower cadence ({cadence.value:.0f} SPM) combined with higher vertical oscillation proxy ({vertical.relative_movement_proxy}).",
                supporting_metrics=[f"Cadence: {cadence.value:.0f} SPM", f"Vertical proxy: {vertical.relative_movement_proxy}"],
                confidence="High",
                scientific_note="Higher vertical bounce increases ground reaction impact; slight cadence increases can smooth vertical displacement."
            ))
        else:
            observations.append(FormPatternObservation(
                label="Stable Cadence Rhythm",
                category="Rhythm",
                reason=f"Measured step rate of {cadence.value:.0f} SPM with consistent inter-step timing.",
                supporting_metrics=[f"Cadence: {cadence.value:.0f} SPM", f"Total steps: {cadence.step_count}"],
                confidence=cadence.confidence,
                scientific_note="Cadence reflects individual leg length, pace, and running surface."
            ))

        # 3. Bilateral Symmetry Rules
        if temporal.symmetry_pct >= 92.0:
            observations.append(FormPatternObservation(
                label="High Bilateral Step Symmetry",
                category="Symmetry",
                reason=f"Bilateral contact timing symmetry is {temporal.symmetry_pct:.1f}% (Left: {temporal.left_mean_step_time_s}s, Right: {temporal.right_mean_step_time_s}s).",
                supporting_metrics=[f"Symmetry: {temporal.symmetry_pct}%", f"Left step: {temporal.left_mean_step_time_s}s", f"Right step: {temporal.right_mean_step_time_s}s"],
                confidence=temporal.confidence,
                scientific_note="Balanced temporal symmetry indicates smooth bilateral gait transition without dominant side-loading."
            ))
        else:
            observations.append(FormPatternObservation(
                label="Observable Bilateral Step Asymmetry",
                category="Symmetry",
                reason=f"Step duration differential observed between left ({temporal.left_mean_step_time_s}s) and right ({temporal.right_mean_step_time_s}s) sides.",
                supporting_metrics=[f"Symmetry: {temporal.symmetry_pct}%"],
                confidence=temporal.confidence,
                scientific_note="Minor asymmetry is common in runners and can reflect lateral dominance, surface camber, or curve navigation."
            ))

        # 4. Foot Strike & Contact Geometry Rules
        if foot_strike.pattern != "Uncertain":
            observations.append(FormPatternObservation(
                label=f"{foot_strike.pattern} Contact",
                category="Foot Strike",
                reason=f"Foot angle at initial contact measured at {foot_strike.mean_strike_angle_deg}° ({foot_strike.observation_summary}).",
                supporting_metrics=[f"Pattern: {foot_strike.pattern}", f"Contact angle: {foot_strike.mean_strike_angle_deg}°"],
                confidence=foot_strike.confidence,
                scientific_note="Foot strike patterns are natural individual adaptations and do not dictate performance in isolation."
            ))

        # 5. Overstriding Indicator Rules
        if "Elevated" in overstride.indicator_status:
            observations.append(FormPatternObservation(
                label="Potential Overstriding Indicator",
                category="Contact Geometry",
                reason=f"Lead foot lands notably ahead of pelvis center with extended knee ({overstride.mean_knee_angle_deg}°).",
                supporting_metrics=[f"Knee angle: {overstride.mean_knee_angle_deg}°", f"Foot lead ratio: {overstride.mean_foot_lead_ratio}"],
                confidence=overstride.confidence,
                scientific_note="Landing closer beneath the center of mass with a slightly flexed knee reduces braking forces."
            ))
        else:
            observations.append(FormPatternObservation(
                label="Efficient Foot Landing Geometry",
                category="Contact Geometry",
                reason=f"Initial contact occurs with compliant knee flexion ({overstride.mean_knee_angle_deg}°) beneath the body center.",
                supporting_metrics=[f"Knee angle: {overstride.mean_knee_angle_deg}°"],
                confidence=overstride.confidence,
                scientific_note="Compliant knee landing cushions ground impact loading naturally."
            ))

        return observations

form_classifier = FormClassifier()
