from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.metrics.cadence_engine import CadenceResult
from app.metrics.temporal_engine import TemporalSymmetryResult
from app.metrics.kinematics_engine import (
    TrunkLeanResult, ArmSwingResult, FootStrikeResult, OverstrideResult, VerticalMovementResult
)
from app.context.running_type_classifier import RunningTypeContext
from app.insights.confidence_engine import MetricConfidenceBreakdown

@dataclass
class ContextAwareInsight:
    title: str
    category: str               # "Cadence", "Symmetry", "Posture", "Foot Strike", "Landing Geometry", "Efficiency"
    severity: str               # "positive", "neutral", "monitor"
    description: str
    supporting_metrics: List[str]
    confidence: str             # "High", "Medium", "Low"
    why_flagged: List[str]      # Itemized explanation for why this was observed/flagged
    recommended_action: str     # Evidence-informed educational recommendation
    limitations: str

@dataclass
class OverallSummaryReport:
    headline: str
    strongest_positive_observations: List[str]
    areas_to_monitor: List[str]
    form_consistency_score: float  # 0 to 100 transparent observational score (NOT injury risk)
    context_summary: str
    responsible_ai_disclaimer: str

class InsightEngine:
    """Generates context-aware, explainable educational insights with non-diagnostic language."""

    @staticmethod
    def generate_insights(
        cadence: CadenceResult,
        temporal: TemporalSymmetryResult,
        trunk: TrunkLeanResult,
        arms: ArmSwingResult,
        foot_strike: FootStrikeResult,
        overstride: OverstrideResult,
        vertical: VerticalMovementResult,
        context: RunningTypeContext,
        confidence_breakdown: MetricConfidenceBreakdown
    ) -> tuple[List[ContextAwareInsight], OverallSummaryReport]:
        insights: List[ContextAwareInsight] = []
        positives: List[str] = []
        monitors: List[str] = []

        # 1. Cadence & Rhythm in Context
        cadence_val = cadence.value
        cad_conf = confidence_breakdown.cadence_confidence.confidence_level

        if 165.0 <= cadence_val <= 185.0:
            sev = "positive"
            positives.append(f"Cadence ({cadence_val:.0f} SPM) is within standard rhythm range for {context.distance_category.lower()}.")
            desc = (
                f"Your cadence is estimated at {cadence_val:.0f} SPM during this {context.intensity_category.lower()} session on {context.surface_category.lower()}. "
                "This step rate promotes efficient ground contact time without excessive vertical oscillation."
            )
            action = "Maintain your natural stride rhythm; cadence will naturally modulate with running speed and terrain changes."
        elif cadence_val < 165.0:
            sev = "monitor"
            monitors.append(f"Cadence ({cadence_val:.0f} SPM) is slightly low for {context.distance_category.lower()}.")
            desc = (
                f"Your cadence was measured at {cadence_val:.0f} SPM. For {context.surface_category.lower()} running at {context.intensity_category.lower()}, "
                "a slightly higher step frequency may help reduce peak braking forces per step."
            )
            action = "Experiment with subtle step rate increases (e.g. +3–5%) using a metronome or music pacing cues while keeping effort easy."
        else:
            sev = "neutral"
            desc = (
                f"Your cadence was measured at {cadence_val:.0f} SPM, representing a quick turnover style. "
                "Higher step frequencies are common during faster training intervals or shorter stride patterns."
            )
            action = "Ensure your upper body remains relaxed and avoid artificially shortening your stride."

        insights.append(ContextAwareInsight(
            title=f"Step Frequency Context ({context.distance_category})",
            category="Cadence",
            severity=sev,
            description=desc,
            supporting_metrics=[
                f"Cadence: {cadence_val:.0f} SPM",
                f"Surface: {context.surface_category}",
                f"Goal: {context.distance_category}"
            ],
            confidence=cad_conf,
            why_flagged=[
                f"Measured {cadence.step_count} foot strikes over {cadence.duration_s:.1f}s",
                f"Contextualized for {context.distance_category} on {context.surface_category}",
                "Evaluated against individualized movement rhythm rather than a universal 180 SPM mandate"
            ],
            recommended_action=action,
            limitations="Cadence from monocular video reflects visible foot contacts; true pacing depends on GPS or track calibration."
        ))

        # 2. Temporal Bilateral Symmetry
        sym_val = temporal.symmetry_pct
        sym_conf = confidence_breakdown.symmetry_confidence.confidence_level

        if sym_val >= 92.0:
            positives.append(f"High bilateral step symmetry ({sym_val:.1f}%) between left and right foot strikes.")
            insights.append(ContextAwareInsight(
                title="Bilateral Stride Symmetry",
                category="Symmetry",
                severity="positive",
                description=(
                    f"Your left/right contact duration symmetry was measured at {sym_val:.1f}%, reflecting balanced weight-shift transitions "
                    f"(Left: {temporal.left_mean_step_time_s}s, Right: {temporal.right_mean_step_time_s}s)."
                ),
                supporting_metrics=[f"Symmetry: {sym_val}%", f"Step CV: {temporal.step_time_variability_cv}%"],
                confidence=sym_conf,
                why_flagged=[
                    f"Left step time: {temporal.left_mean_step_time_s}s vs Right step time: {temporal.right_mean_step_time_s}s",
                    f"Bilateral difference is only {abs(temporal.left_mean_step_time_s - temporal.right_mean_step_time_s):.3f}s"
                ],
                recommended_action="Continue your current strength and mobility routine to support bilateral coordination.",
                limitations="Temporal symmetry reflects time duration only and does not measure ground impact force in Newtons."
            ))
        else:
            monitors.append(f"Observable bilateral step timing difference (Symmetry: {sym_val:.1f}%).")
            insights.append(ContextAwareInsight(
                title="Bilateral Timing Observation",
                category="Symmetry",
                severity="monitor",
                description=(
                    f"A step duration difference was observed ({temporal.left_mean_step_time_s}s left vs {temporal.right_mean_step_time_s}s right, {sym_val:.1f}% symmetry). "
                    "Small asymmetries are common in runners due to road camber, dominant leg preference, or subtle fatigue."
                ),
                supporting_metrics=[f"Symmetry: {sym_val}%", f"Left: {temporal.left_mean_step_time_s}s", f"Right: {temporal.right_mean_step_time_s}s"],
                confidence=sym_conf,
                why_flagged=[
                    f"Inter-step differential exceeds 5% ({abs(temporal.left_mean_step_time_s - temporal.right_mean_step_time_s):.3f}s delta)",
                    "Observed across multiple consecutive step cycles"
                ],
                recommended_action="Consider monitoring whether this pattern persists on flat treadmill or track surfaces. Discuss with a qualified professional if symptoms or discomfort are present.",
                limitations="Asymmetry is an observational kinematic measurement and is NOT an injury diagnosis."
            ))

        # 3. Sagittal Trunk Posture
        trunk_val = trunk.mean_trunk_lean_deg
        trunk_conf = confidence_breakdown.trunk_lean_confidence.confidence_level

        if 4.0 <= trunk_val <= 11.0:
            positives.append(f"Forward torso lean ({trunk_val:.1f}°) promotes momentum alignment.")
            t_sev = "positive"
            t_desc = f"Your average trunk forward inclination is {trunk_val:.1f}°, falling within the recommended 4–11° range for efficient forward propulsion."
            t_action = "Maintain whole-body forward lean originating from the ankles rather than bending at the waist."
        elif trunk_val < 4.0:
            t_sev = "neutral"
            t_desc = f"Your trunk is relatively upright ({trunk_val:.1f}°). While upright postures are common, a subtle forward lean can assist forward hip extension."
            t_action = "Cue yourself to lean forward slightly from the ankles as if running with a gentle tailwind."
        else:
            monitors.append(f"Pronounced forward torso inclination ({trunk_val:.1f}°).")
            t_sev = "monitor"
            t_desc = f"Your forward trunk lean measured {trunk_val:.1f}°. Pronounced forward torso angles may increase lumbar and hamstring muscular demand."
            t_action = "Focus on tall spine posture and engaging your core to stabilize the pelvis."

        insights.append(ContextAwareInsight(
            title="Sagittal Posture & Trunk Inclination",
            category="Posture",
            severity=t_sev,
            description=t_desc,
            supporting_metrics=[f"Trunk lean: {trunk_val}°", f"Range: {trunk.min_lean_deg}°–{trunk.max_lean_deg}°"],
            confidence=trunk_conf,
            why_flagged=[
                f"Mean torso vector relative to vertical: {trunk_val}°",
                f"Variability: ±{trunk.variability_deg}° across gait cycles"
            ],
            recommended_action=t_action,
            limitations="Estimated from 2D camera projection plane. Camera perspective angles may introduce minor projection offset."
        ))

        # 4. Foot Strike & Landing Geometry
        fs_pattern = foot_strike.pattern
        fs_conf = confidence_breakdown.foot_strike_confidence.confidence_level

        insights.append(ContextAwareInsight(
            title=f"Foot Contact Pattern ({fs_pattern})",
            category="Foot Strike",
            severity="neutral",
            description=(
                f"Your recording is consistent with a {fs_pattern.lower()} landing pattern (foot contact angle: {foot_strike.mean_strike_angle_deg}°). "
                "Foot-strike patterns naturally redistribute impact load across the foot, calf, and knee, and are not inherently good or bad."
            ),
            supporting_metrics=[f"Pattern: {fs_pattern}", f"Contact angle: {foot_strike.mean_strike_angle_deg}°"],
            confidence=fs_conf,
            why_flagged=[
                f"Ankle-to-toe angle at initial contact: {foot_strike.mean_strike_angle_deg}°",
                f"Evidence: {foot_strike.observation_summary}"
            ],
            recommended_action="Do not attempt to drastically alter your foot strike pattern unless specifically guided by a sports physiotherapist.",
            limitations="2D visual estimation proxy. True plantar pressure distribution requires calibrated laboratory equipment."
        ))

        # 5. Potential Overstride Indicator
        over_status = overstride.indicator_status
        over_conf = confidence_breakdown.overstride_confidence.confidence_level

        if "Elevated" in over_status:
            monitors.append("Lead foot lands ahead of pelvis center at initial contact.")
            o_sev = "monitor"
            o_desc = (
                f"A potential overstriding indicator was flagged (knee angle {overstride.mean_knee_angle_deg}° with extended foot lead). "
                "Landing with the foot far ahead of the center of mass may increase braking forces."
            )
            o_action = "Experiment with slightly shorter steps and cue your feet to land closer beneath your hips."
        else:
            positives.append(f"Compliant landing geometry ({overstride.mean_knee_angle_deg}° knee flexion at contact).")
            o_sev = "positive"
            o_desc = f"Initial contact occurs with compliant knee flexion ({overstride.mean_knee_angle_deg}°), helping naturally cushion initial ground impact."
            o_action = "Maintain your current step landing position."

        insights.append(ContextAwareInsight(
            title="Landing Geometry & Overstride Indicator",
            category="Landing Geometry",
            severity=o_sev,
            description=o_desc,
            supporting_metrics=[f"Knee angle: {overstride.mean_knee_angle_deg}°", f"Foot lead ratio: {overstride.mean_foot_lead_ratio}"],
            confidence=over_conf,
            why_flagged=overstride.supporting_observations,
            recommended_action=o_action,
            limitations="Observational indicator only. Not an injury prediction or clinical diagnosis."
        ))

        # Overall Form Consistency Score calculation (0 to 100)
        # Based on symmetry (35%), stride consistency (25%), posture alignment (20%), video tracking confidence (20%)
        score_val = round(
            0.35 * min(100.0, sym_val) +
            0.25 * max(50.0, 100.0 - temporal.step_time_variability_cv * 5.0) +
            0.20 * (95.0 if 4.0 <= trunk_val <= 11.0 else 80.0) +
            0.20 * confidence_breakdown.overall_score,
            1
        )

        overall_report = OverallSummaryReport(
            headline=f"Biomechanical Observation Summary ({context.distance_category})",
            strongest_positive_observations=positives or ["Consistent step frequency across recording."],
            areas_to_monitor=monitors or ["Maintain current balanced movement rhythm."],
            form_consistency_score=score_val,
            context_summary=context.runner_profile_summary,
            responsible_ai_disclaimer="MotionIQ provides observational kinematic estimates for educational guidance. It does NOT diagnose injuries or replace clinical gait analysis."
        )

        return insights, overall_report

insight_engine = InsightEngine()
